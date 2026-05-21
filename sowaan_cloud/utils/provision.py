import frappe # type: ignore
import subprocess
import os
import requests
import re
from sowaan_cloud.utils.cloud_settings import get_cloud_settings
import json
import pwd
from datetime import datetime
from datetime import date, timedelta

import base64
import json
from frappe.utils import get_url # type: ignore

def frappe_user_exists():
    try:
        pwd.getpwnam("frappe")
        return True
    except KeyError:
        return False
    
@frappe.whitelist()
def create_instance(docname):
    doc = frappe.get_doc("Cloud Subscription", docname)

    doc.provisioning_logs = ""
    # 4️⃣ Mark provisioning & enqueue
    doc.status = "Provisioning"
    doc.save(ignore_permissions=True)

    frappe.enqueue(
        "sowaan_cloud.utils.provision.provision_from_subscription",
        queue="long",
        docname=docname,
        timeout=3600,
        is_async=True,
    )

def provision_from_subscription(docname):
    sub = frappe.get_doc("Cloud Subscription", docname) if isinstance(docname, str) else docname

    if not sub.site_name:
        sub.site_name = f"{sub.instance_name}.{settings.your_site_name_suffix}"
        sub.save(ignore_permissions=True)
    site_name = sub.site_name

    settings = get_cloud_settings()
    bench_path = settings.bench_path
    sql_password = settings.get_password("sql_password")  # Replace with actual DB root password
    site_path = os.path.join(bench_path, "sites", site_name)

    try:
        # 🔒 Lock intent only (DO NOT RESET STEP)
        if sub.status not in ("Provisioning", "Active"):
            sub.status = "Provisioning"
            sub.save(ignore_permissions=True)

        # 1️⃣ SITE
        if sub.provisioning_step in (None, "INIT"):
            create_site_if_missing(site_name, bench_path, sql_password)
            update_subscription_state(sub, step="SITE_CREATED")

        # 2️⃣ APPS
        if sub.provisioning_step == "SITE_CREATED":
            pkg = frappe.get_doc("Cloud Package", sub.selected_package)
            ensure_apps(site_name, bench_path, [row.app_name for row in pkg.apps])
            enforce_site_config(site_path, {"skip_setup_wizard": 1})
            trial_days = settings.trial_days or 15
            enforce_trial_validity(site_path, trial_days)
            update_subscription_state(sub, step="APPS_INSTALLED")

        # 3️⃣ BOOTSTRAP
        if sub.provisioning_step == "APPS_INSTALLED":
            

            bootstrap_site(site_name, sub)
            update_subscription_state(sub, step="BOOTSTRAPPED")

        # 4️⃣ COMPLETE
        if sub.provisioning_step == "BOOTSTRAPPED":
            run_migrate(site_name, bench_path)
            create_cloudflare_dns(site_name)
        
            frappe.enqueue(
                "sowaan_cloud.utils.ssl.issue_ssl_async",
                queue="long",
                site_name=site_name,
                docname=sub.name,
                timeout=900,
            )


            update_subscription_state(
                sub,
                status="Active",
                step="COMPLETED",
            )

    except Exception as e:
        raw = getattr(e, "output_combined", None) or getattr(e, "stderr", None) or str(e)
        err = analyze_provisioning_error(raw)
        update_subscription_state(
            sub,
            status="Failed",
            step=sub.provisioning_step,
            error=f"{err['message']}\n\n{raw}",
        )

        raise


def get_branding_payload(sub):
    base_url = get_url()  # sowaan.cloud (or whatever panel site)

    def abs_url(path):
        if not path:
            return None
        if path.startswith("http"):
            return path
        return base_url.rstrip("/") + path

    settings = get_cloud_settings()

    return {
        "logo_file_url": abs_url(sub.company_logo),
        "header_file_url": abs_url(sub.letterhead_header),
        "footer_file_url": abs_url(sub.letterhead_footer),
        "brand_name": sub.company_name,
        "create_letterhead": settings.create_letterhead,
    }



def create_site_if_missing(site_name, bench_path, sql_password):
    site_path = os.path.join(bench_path, "sites", site_name)

    if os.path.isdir(site_path):
        frappe.logger("provisioning").info(
            f"[SITE] Already exists: {site_name}"
        )
        return False  # not created

    frappe.logger("provisioning").info(
        f"[SITE] Creating new site: {site_name}"
    )

    run_as_frappe(
        f"bench new-site {site_name} "
        f"--admin-password admin "
        f"--db-root-password {sql_password}",
        bench_path,
    )

    return True  # created

def get_installed_apps(site_name, bench_path):
    result = run_as_frappe(
        f"bench --site {site_name} list-apps",
        bench_path,
        capture_output=True,
    )

    if not result or not result.stdout:
        return set()

    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    }



def ensure_apps(site_name, bench_path, apps_to_install):
    installed = get_installed_apps(site_name, bench_path)

    for app in apps_to_install:
        if app in installed:
            frappe.logger("provisioning").info(
                f"[APPS] {app} already installed, skipping"
            )
            continue

        frappe.logger("provisioning").info(
            f"[APPS] Installing {app}"
        )

        run_as_frappe(
            f"bench --site {site_name} install-app {app}",
            bench_path,
        )

def enforce_site_config(site_path, updates=None):
    if updates is None:
        updates = {}

    config_path = os.path.join(site_path, "site_config.json")

    if not os.path.exists(config_path):
        frappe.throw("site_config.json not found")

    with open(config_path) as f:
        config = json.load(f)

    changed = False
    for key, value in updates.items():
        if config.get(key) != value:
            config[key] = value
            changed = True

    if changed:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        frappe.logger("provisioning").info(
            f"[CONFIG] site_config.json updated"
        )

def enforce_trial_validity(site_path, days):
    valid_till = (date.today() + timedelta(days=days)).isoformat()

    enforce_site_config(site_path, {
        "trial_valid_till": valid_till,
    })
    enforce_site_config(site_path, {
        "valid_till": valid_till,
    })

    frappe.logger("provisioning").info(
        f"[TRIAL] Valid till {valid_till}"
    )

def bootstrap_site(site_name, doc):
    settings = get_cloud_settings()
    user_password = doc.get_password("user_password")
    # branding = get_branding_payload(doc)
    branding = None

    pkg = frappe.get_doc("Cloud Package", doc.selected_package)

    kwargs = {
        "company_name": doc.company_name,
        "abbr": doc.abbr,
        "country": doc.country,
        "currency": doc.currency,
        "user_email": doc.user_email,
        "user_password": user_password,
        "package": doc.selected_package,
        "modules": [row.module_name for row in pkg.modules],
        "roles": [row.role for row in pkg.roles],
        "branding": branding,
    }

    kwargs_json = json.dumps(kwargs)
    kwargs_b64 = base64.b64encode(kwargs_json.encode()).decode()

    safe_kwargs = json.dumps({"kwargs_b64": kwargs_b64})
    bench_path = settings.bench_path

    run_as_frappe(
        f"bench --site {site_name} execute "
        f"sowaan_client.sowaan_client.run.bootstrap_site "
        f"--kwargs '{safe_kwargs}'",
        bench_path,
    )


def run_migrate(site_name, bench_path):
    frappe.logger("provisioning").info(
        f"[MIGRATE] Running migrations for {site_name}"
    )

    run_as_frappe(
        f"bench --site {site_name} migrate",
        bench_path,
    )

def append_log(sub, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sub.provisioning_logs = (
        (sub.provisioning_logs or "") + f"\n[{ts}] {message}"
    )
    sub.save(ignore_permissions=True)

def update_subscription_state(sub, status=None, step=None, error=None):
    if status:
        sub.status = status
    if step:
        sub.provisioning_step = step
    if error:
        sub.provisioning_logs = error

    sub.save(ignore_permissions=True)
    append_log(sub, f"{sub.provisioning_step}")
    frappe.db.commit()

def run_as_frappe(cmd, bench_path, capture_output=False):
    bench_path = os.path.abspath(bench_path)
    full_cmd = f"cd {bench_path} && {cmd}"

    # always capture both so errors from bench execute (which writes to stdout) are visible
    run_kwargs = {
        "text": True,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }

    try:
        if frappe_user_exists():
            result = subprocess.run(
                ["sudo", "-u", "frappe", "bash", "-lc", full_cmd],
                check=True,
                **run_kwargs,
            )
        else:
            result = subprocess.run(
                ["bash", "-lc", full_cmd],
                check=True,
                **run_kwargs,
            )

        if result.stdout:
            frappe.logger("provisioning").info(result.stdout)

        return result

    except subprocess.CalledProcessError as e:
        output = "\n".join(filter(None, [e.stdout, e.stderr]))
        frappe.logger("provisioning").error(f"[CMD FAILED] {cmd}\n{output}")
        # attach combined output so provision_from_subscription can log it
        e.output_combined = output
        raise




# def run_as_frappe(cmd, bench_path, capture_output=False):
#     """
#     Run bench command as frappe user if available,
#     otherwise run as current user.
#     """

#     bench_path = os.path.abspath(bench_path)

#     full_cmd = f"cd {bench_path} && {cmd}"

#     if frappe_user_exists():
#         subprocess.run(
#             ["sudo", "-u", "frappe", "bash", "-lc", full_cmd],
#             check=True,
#             capture_output=capture_output,
#         )
#     else:
#         # fallback: current user
#         subprocess.run(
#             ["bash", "-lc", full_cmd],
#             check=True,
#             capture_output=capture_output,
#         )



# def run_migrate(site_name, bench_path=None):
#     subprocess.run(
#         ["bench", "--site", site_name, "migrate"],
#         cwd=bench_path,
#         check=True,
#     )

#     # 🔥 CRITICAL: reload framework state
#     subprocess.run(
#         ["bench", "restart"],
#         cwd=bench_path,
#         check=True,
#     )



def analyze_provisioning_error(raw_error: str) -> dict:
    """
    Returns a structured, safe error response
    """
    error = raw_error.lower() if raw_error else ""

    # --- DB AUTH ERRORS ---
    if "access denied for user" in error or "1045" in error:
        return {
            "code": "DB_AUTH_FAILED",
            "title": "Database Authentication Failed",
            "message": (
                "Unable to connect to the database using the configured credentials.\n\n"
                "Please verify:\n"
                "• Database user exists\n"
                "• Password is correct\n"
                "• User has sufficient privileges"
            ),
            "severity": "error",
        }

    # --- SITE EXISTS ---
    if "already exists" in error:
        return {
            "code": "SITE_EXISTS",
            "title": "Site Already Exists",
            "message": (
                "The site already exists on the server and cannot be created again.\n"
                "The existing site can be reused."
            ),
            "severity": "info",
        }

    # --- PERMISSION ERRORS ---
    if "permission denied" in error:
        return {
            "code": "PERMISSION_DENIED",
            "title": "Permission Denied",
            "message": (
                "The system does not have sufficient permissions to complete provisioning.\n"
                "Please check file system and database permissions."
            ),
            "severity": "error",
        }

    # --- FALLBACK ---
    return {
        "code": "UNKNOWN_ERROR",
        "title": "Provisioning Failed",
        "message": (
            "An unexpected error occurred during provisioning.\n"
            "Please contact support or check server logs."
        ),
        "severity": "error",
    }

def cloudflare_headers(settings):
    token = settings.get_password("cloudflare_api_secret")

    if not token:
        frappe.throw("Cloudflare API token is missing")

    return {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
    }

def cloudflare_dns_exists(site_name):
    settings = get_cloud_settings()
    headers = cloudflare_headers(settings)
    zone_id = settings.get_password("cloudflare_zone_domain")

    r = requests.get(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
        headers=headers,
        params={"name": site_name},
        timeout=10,
    )
    data = r.json()
    return bool(data.get("result"))

def create_cloudflare_dns(site_name):
    settings = get_cloud_settings()

    if not settings.enable_dns:
        return

    if cloudflare_dns_exists(site_name):
        frappe.logger("provisioning").info(
            f"[DNS] Record already exists: {site_name}"
        )
        return
    
    zone_id = settings.get_password("cloudflare_zone_domain")

    headers = cloudflare_headers(settings)

    payload = {
        "type": "A",
        "name": site_name,
        "content": settings.server_ip,
        "ttl": 120,
        "proxied": False,
    }

    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"

    r = requests.post(url, json=payload, headers=headers, timeout=10)
    data = r.json()

    # frappe.log_error("DNS Creation Result", f"data values: \n{data}")
    if not data.get("success"):
        raise Exception(data)
