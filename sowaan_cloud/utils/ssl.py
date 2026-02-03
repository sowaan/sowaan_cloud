import time
import socket
import subprocess
import frappe # type: ignore
from sowaan_cloud.utils.cloud_settings import get_cloud_settings
import os
from sowaan_cloud.utils.provision import run_as_frappe

MAX_SSL_ATTEMPTS = 3


def wait_for_dns(site_name, expected_ip, timeout=120, interval=5):
    start = time.time()

    while time.time() - start < timeout:
        try:
            resolved_ip = socket.gethostbyname(site_name)
            if resolved_ip == expected_ip:
                return True
        except socket.gaierror:
            pass

        time.sleep(interval)

    # raise Exception("DNS not propagated")
    return False


def ssl_exists(site_name):
    return os.path.exists(
        f"/etc/letsencrypt/live/{site_name}/fullchain.pem"
    )

def issue_ssl(site_name, bench_path):
    try:
        result = run_as_frappe(
            f"bench setup lets-encrypt {site_name}",
            bench_path,
            capture_output=True,
        )

        frappe.logger("provisioning").info(
            f"[SSL] LetsEncrypt output for {site_name}\n{result.stdout}"
        )

    except subprocess.CalledProcessError as e:
        frappe.logger("provisioning").error(
            f"""
                [SSL ERROR] LetsEncrypt failed for {site_name}

                COMMAND:
                bench setup lets-encrypt {site_name}

                STDOUT:
                {e.stdout}

                STDERR:
                {e.stderr}
                """
        )
        raise

    
# def issue_ssl(site_name):
#     settings = get_cloud_settings()

#     subprocess.run(
#         [
#             "sudo",
#             "certbot",
#             "--nginx",
#             "-d", site_name,
#             "--non-interactive",
#             "--agree-tos",
#             "-m", settings.ssl_email or f"admin@{settings.site_suffix}",
#             "--redirect",
#         ],
#         check=True,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         text=True,
#     )

def retry_failed_ssl():
    """
    Retry SSL issuance for failed or pending sites.
    Runs via scheduler.
    """

    for d in frappe.get_all(
        "Cloud Subscription",
        filters={
            "ssl_status": ["in", ["Failed", "Pending"]],
            "provisioned": 1,
        },
        fields=["name", "site_name", "ssl_attempts"],
    ):
        if not d.site_name:
            continue

        frappe.enqueue(
            "sowaan_cloud.utils.ssl.issue_ssl_async",
            queue="long",
            site_name=d.site_name,
            docname=d.name,
            timeout=900,
        )


def issue_ssl_async(site_name, docname):
    """
    Background SSL worker.
    Safe, idempotent, retry-aware.
    """

    settings = get_cloud_settings()
    doc = frappe.get_doc("Cloud Subscription", docname)

    if not settings.enable_ssl:
        return

    # Already secured?
    if ssl_exists(site_name):
        doc.ssl_status = "Issued"
        doc.save(ignore_permissions=True)
        return

    doc.ssl_attempts = (doc.ssl_attempts or 0) + 1
    doc.save(ignore_permissions=True)

    try:
        # 1️⃣ Wait for DNS
        wait_for_dns(site_name, settings.server_ip)

        # 2️⃣ Issue SSL
        issue_ssl(site_name, settings.bench_path)

        doc.ssl_status = "Issued"
        doc.ssl_last_error = ""
        doc.save(ignore_permissions=True)

    except Exception as e:
        # 🔥 Log full traceback (VERY IMPORTANT)
        frappe.logger("provisioning").exception(
            f"[SSL] Failed for site {site_name}"
        )
        

        # 📌 Update subscription status
        doc.ssl_status = "Failed"
        doc.ssl_last_error = str(e)
        doc.save(ignore_permissions=True)

        # 🔁 Retry later if attempts remain
        if doc.ssl_attempts < MAX_SSL_ATTEMPTS:
            frappe.enqueue(
                "sowaan_cloud.utils.ssl.issue_ssl_async",
                queue="long",
                site_name=site_name,
                docname=docname,
                timeout=900,
                enqueue_after_commit=True,
                at_front=False,
            )
