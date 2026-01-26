import frappe
import subprocess
import shlex
import os
import requests
import re
from sowaan_cloud.utils.cloud_settings import get_cloud_settings


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

    # 3️⃣ Safety check: site already exists on disk
    if os.path.exists(site_path):
        doc.site_name = site_name
        doc.provisioned = 1
        doc.status = "Active"
        doc.save(ignore_permissions=True)

        frappe.msgprint(
            "Site already exists. Linked existing instance.",
            indicator="green",
        )
        return

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
        if not os.path.isdir(site_path):
            subprocess.run(
                [
                    "bench",
                    "new-site",
                    site_name,
                    "--admin-password", "admin",
                    "--db-root-password", SQL_PASSWORD,
                ],
                cwd=BENCH_PATH,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        # 2️⃣ Install apps (safe to re-run)
        for app in ("erpnext", "zatca", "sowaan_cloud"):
            subprocess.run(
                ["bench", "--site", site_name, "install-app", app],
                cwd=BENCH_PATH,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        # 3️⃣ Bootstrap (safe if idempotent)
        subprocess.run(
            [
                "bench",
                "--site", site_name,
                "execute",
                "sowaan_cloud.utils.bootstrap.bootstrap_site",
                "--kwargs",
                f'{{"company_name": "{doc.company_name}", "abbr": "{doc.abbr}"}}'
            ],
            cwd=BENCH_PATH,
            check=True,
        )

        # 4️⃣ DNS + SSL (idempotent)
        create_cloudflare_dns(site_name)
        issue_ssl(site_name)

        # 5️⃣ NOW mark active (only here)
        doc.site_name = site_name
        doc.status = "Active"
        doc.provisioned = 1
        doc.save(ignore_permissions=True)


    except Exception as e:
        raw_error = str(e)
        sanitized_error = sanitize_raw_error(raw_error)
        analyzed = analyze_provisioning_error(raw_error)

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
        "Authorization": f"Bearer {settings.get_password('cloudflare_api_token')}",
        "Content-Type": "application/json",
    }

    url = (
        f"https://api.cloudflare.com/client/v4/zones/"
        f"{settings.cloudflare_zone_id}/dns_records"
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
        "Authorization": f"Bearer {settings.get_password('cloudflare_api_token')}",
        "Content-Type": "application/json",
    }

    payload = {
        "type": "A",
        "name": site_name,
        "content": settings.server_ip,
        "ttl": 120,
        "proxied": False,
    }

    url = f"https://api.cloudflare.com/client/v4/zones/{settings.cloudflare_zone_id}/dns_records"

    r = requests.post(url, json=payload, headers=headers, timeout=10)
    data = r.json()

    if not data.get("success"):
        raise Exception(data)

def ssl_exists(site_name):
    return os.path.exists(f"/etc/letsencrypt/live/{site_name}/fullchain.pem")

def issue_ssl(site_name):
    settings = get_cloud_settings()

    if not settings.enable_ssl:
        return

    if ssl_exists(site_name):
        return  # ✅ Already secured

    subprocess.run(
        [
            "certbot",
            "--nginx",
            "-d", site_name,
            "--non-interactive",
            "--agree-tos",
            "-m", f"admin@{settings.site_suffix}",
            "--redirect",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
