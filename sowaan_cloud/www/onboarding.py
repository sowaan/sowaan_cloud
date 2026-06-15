import json
import os
import frappe

no_cache = 1


def get_context(context):
    manifest_path = frappe.get_app_path(
        "sowaan_cloud", "public", "onboarding", ".vite", "manifest.json"
    )

    js_file = None
    css_file = None

    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)

        for entry in manifest.values():
            if entry.get("isEntry"):
                js_file = f"/assets/sowaan_cloud/onboarding/{entry['file']}"
                for css in entry.get("css", []):
                    css_file = f"/assets/sowaan_cloud/onboarding/{css}"
                break

    context.js_file = js_file
    context.css_file = css_file
