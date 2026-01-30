import frappe # type: ignore
import subprocess
import os
import requests
import re
from sowaan_cloud.utils.cloud_settings import get_cloud_settings
import json
import subprocess
import pwd


def os_user_exists(username: str) -> bool:
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False


@frappe.whitelist()
def create_instance(docname):
    settings = get_cloud_settings()

    BENCH_PATH = settings.bench_path
    SITE_SUFFIX = settings.site_suffix

    doc = frappe.get_doc("Cloud Subscription", docname)

    # 1️⃣ Prevent double provisioning
    if doc.status == "Provisioning":
        frappe.throw("Instance provisioning is already in progress.")

    # 2️⃣ If already provisioned, do nothing
    if doc.provisioned:
        frappe.throw("Instance already provisioned.")

    site_name = f"{doc.instance_name}.{SITE_SUFFIX}"
    site_path = os.path.join(BENCH_PATH, "sites", site_name)

    doc.provisioning_logs = ""
    # 4️⃣ Mark provisioning & enqueue
    doc.status = "Provisioning"
    doc.save(ignore_permissions=True)

    frappe.enqueue(
        "sowaan_cloud.utils.provision.run_bench_provisioning",
        queue="long",
        docname=docname,
        timeout=3600,
        is_async=True,
    )

def run_as_frappe(cmd: str, bench_path: str):
    """
    Run a bench command:
    - As frappe user if present
    - Otherwise as current user
    Always via login shell to load env
    """

    full_cmd = f"cd {bench_path} && {cmd}"

    if os_user_exists("frappe"):
        subprocess.run(
            ["sudo", "-u", "frappe", "bash", "-lc", full_cmd],
            check=True,
        )
    else:
        # Dev / CI fallback
        subprocess.run(
            ["bash", "-lc", full_cmd],
            check=True,
        )

def run_bench_provisioning(docname):
    settings = get_cloud_settings()
    BENCH_PATH = settings.bench_path
    SITE_SUFFIX = settings.site_suffix
    SQL_PASSWORD = settings.get_password("sql_password")  # Replace with actual DB root password

    doc = frappe.get_doc("Cloud Subscription", docname)
    site_name = doc.instance_name + "." + SITE_SUFFIX

    site_path = os.path.join(BENCH_PATH, "sites", site_name)

    try:
        # 1️⃣ Create site if missing
        # if not os.path.isdir(site_path):
        #     subprocess.run(
        #         [
        #             "bench",
        #             "new-site",
        #             site_name,
        #             "--admin-password", "admin",
        #             "--db-root-password", SQL_PASSWORD,
        #         ],
        #         cwd=BENCH_PATH,
        #         check=True,
        #         stdout=subprocess.PIPE,
        #         stderr=subprocess.PIPE,
        #         text=True,
        #     )
        run_as_frappe(
            f"bench new-site {site_name} "
            f"--admin-password admin "
            f"--db-root-password {SQL_PASSWORD}",
            BENCH_PATH,
        )
        enforce_site_config(site_path)

        # 2️⃣ Install apps (safe to re-run)
        for app in ("erpnext", "zatca", "sowaan_cloud", "sowaanerp_subscription"):
            run_as_frappe(
                f"bench --site {site_name} install-app {app}",
                BENCH_PATH,
            )

        
        
        # 3️⃣ Bootstrap (safe if idempotent)
        
        kwargs = {
            "company_name": doc.company_name,
            "abbr": doc.abbr,
            "user_email": doc.user_email,
            "country": doc.country,
            "currency": doc.currency,
        }

        kwargs_json = json.dumps(kwargs).replace('"', '\\"')

        run_as_frappe(
            f'bench --site {site_name} execute '
            f'sowaan_cloud.utils.bootstrap.bootstrap_site '
            f'--kwargs "{kwargs_json}"',
            BENCH_PATH,
        )

        # if result.returncode != 0:
        #     frappe.log_error(
        #         title="Bootstrap Failed",
        #         message=(
        #             f"STDOUT:\n{result.stdout}\n\n"
        #             f"STDERR:\n{result.stderr}"
        #         ),
        #     )
        #     raise Exception("bootstrap_site failed")

        # 4️⃣ DNS + SSL (idempotent)
        create_cloudflare_dns(site_name)
        # issue_ssl_with_wait(site_name)

        # 5️⃣ NOW mark active (only here)
        doc.site_name = site_name
        doc.status = "Active"
        doc.provisioned = 1
        doc.save(ignore_permissions=True)

        frappe.enqueue(
            "sowaan_cloud.utils.ssl.issue_ssl_async",
            queue="long",
            site_name=site_name,
            docname=doc.name,
            timeout=900,
        )
        run_migrate(site_name, bench_path=BENCH_PATH)


    except Exception as e:
        raw_error = str(e)
        sanitized_error = sanitize_raw_error(raw_error)
        analyzed = analyze_provisioning_error(raw_error)

        frappe.log_error(
                    frappe.get_traceback(),
                    "BOOTSTRAP SITE FAILED"
                )
        # Save ONLY sanitized / friendly info
        doc.status = "Failed"
        doc.provisioning_logs = analyzed["message"]
        doc.save(ignore_permissions=True)

        # Log minimal safe info
        frappe.log_error(
            title=f"Provisioning Failed [{analyzed['code']}]",
            message=f"actual error: {raw_error}\n\nsanitized error: {sanitized_error}",
        )
        # frappe.log_error(
        #     title=f"Provisioning Failed [{analyzed['code']}]",
        #     message=analyzed["message"],
        # )
        # Optional: keep full error ONLY in server logs
        frappe.logger("provisioning").error(sanitized_error)

        # Raise safe error (no traceback, no secrets)
        # frappe.throw(
        #     analyzed["message"],
        #     title=analyzed["title"],
        # )

def enforce_site_config(site_path):
    path = os.path.join(site_path, "site_config.json")

    with open(path) as f:
        config = json.load(f)

    config["skip_setup_wizard"] = 1

    with open(path, "w") as f:
        json.dump(config, f, indent=2)

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
def run_migrate(site_name, bench_path):
    """
    Run migrate in a login shell so environment matches manual execution.
    """

    cmd = (
        f"cd {bench_path} && "
        f"bench --site {site_name} migrate && "
        f"bench restart"
    )

    subprocess.run(
        ["bash", "-lc", cmd],
        check=True,
    )


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


def sanitize_raw_error(text: str) -> str:
    if not text:
        return ""

    patterns = [
        r"--db-root-password\s+\S+",
        r"--password\s+\S+",
        r"password:\s*\S+",
    ]

    for p in patterns:
        text = re.sub(p, "--db-root-password ******", text)

    return text

def cloudflare_dns_exists(site_name):
    settings = get_cloud_settings()

    headers = {
        "Authorization": f"Bearer {settings.get_password('cloudflare_api_secret')}",
        "Content-Type": "application/json",
    }

    url = (
        f"https://api.cloudflare.com/client/v4/zones/"
        f"{settings.get_password('cloudflare_zone_domain')}/dns_records"
        f"?type=A&name={site_name}"
    )

    r = requests.get(url, headers=headers, timeout=10)
    data = r.json()

    return data.get("success") and len(data.get("result", [])) > 0

def create_cloudflare_dns(site_name):
    settings = get_cloud_settings()

    if not settings.enable_dns:
        return

    if cloudflare_dns_exists(site_name):
        return  # ✅ Safe retry

    headers = {
        "Authorization": f"Bearer {settings.get_password('cloudflare_api_secret')}",
        "Content-Type": "application/json",
    }

    payload = {
        "type": "A",
        "name": site_name,
        "content": settings.server_ip,
        "ttl": 120,
        "proxied": False,
    }

    url = f"https://api.cloudflare.com/client/v4/zones/{settings.get_password('cloudflare_zone_domain')}/dns_records"

    r = requests.post(url, json=payload, headers=headers, timeout=10)
    data = r.json()

    if not data.get("success"):
        raise Exception(data)

