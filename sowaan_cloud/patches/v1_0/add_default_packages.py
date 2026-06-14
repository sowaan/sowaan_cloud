import frappe

PACKAGES = [
    {
        "package_name": "ZATCA_STARTER",
        "title": "ZATCA Starter",
        "price": 0,
        "users_limit": 5,
        "description": (
            "<b>ZATCA Starter Package</b>"
            "<ul>"
            "<li>ZATCA Phase 2 onboarding</li>"
            "<li>B2B &amp; B2C invoices</li>"
            "<li>KSA Chart of Accounts</li>"
            "<li>Single warehouse stock</li>"
            "</ul>"
        ),
        "apps": ["erpnext", "zatca", "sowaan_client", "sowaanerp_subscription", "ksa_print_formats"],
        "modules": ["Selling", "Buying", "Accounts", "Stock"],
        "roles": ["Sales User", "Purchase User", "Accounts User", "Stock User"],
    },
    {
        "package_name": "ZATCA_RETAIL_POS",
        "title": "ZATCA Retail POS",
        "price": 0,
        "users_limit": 10,
        "description": (
            "<b>ZATCA Retail &amp; POS</b>"
            "<ul>"
            "<li>Everything in Starter</li>"
            "<li>POS setup (single outlet)</li>"
            "<li>Live ZATCA clearance</li>"
            "</ul>"
        ),
        "apps": ["erpnext", "zatca", "sowaan_client", "sowaanerp_subscription", "ksa_print_formats", "posawesome"],
        "modules": ["Selling", "Buying", "Accounts", "Stock", "POS"],
        "roles": ["Sales User", "Purchase User", "Accounts User", "Stock User", "POS User"],
    },
    {
        "package_name": "ZATCA_COMPLETE_SME",
        "title": "ZATCA Complete SME",
        "price": 0,
        "users_limit": 0,
        "description": (
            "<b>ZATCA Complete SME</b>"
            "<ul>"
            "<li>Multi warehouse</li>"
            "<li>VAT, AR/AP</li>"
            "<li>Full accounting</li>"
            "<li>Projects &amp; CRM</li>"
            "<li>Asset management</li>"
            "</ul>"
        ),
        "apps": ["erpnext", "zatca", "sowaan_client", "sowaanerp_subscription", "ksa_print_formats", "posawesome"],
        "modules": ["Selling", "Buying", "Accounts", "Stock", "POS", "Assets", "Projects", "CRM"],
        "roles": ["Sales User", "Purchase User", "Accounts User", "Stock User", "POS User", "Projects User", "CRM User"],
    },
]


def execute():
    for pkg in PACKAGES:
        if frappe.db.exists("Cloud Package", pkg["package_name"]):
            doc = frappe.get_doc("Cloud Package", pkg["package_name"])
            doc.title = pkg["title"]
            doc.price = pkg.get("price", 0)
            doc.users_limit = pkg.get("users_limit", 0)
            doc.description = pkg.get("description", "")
            doc.save(ignore_permissions=True)
        else:
            doc = frappe.get_doc({
                "doctype": "Cloud Package",
                "package_name": pkg["package_name"],
                "title": pkg["title"],
                "price": pkg.get("price", 0),
                "users_limit": pkg.get("users_limit", 0),
                "description": pkg.get("description", ""),
                "apps": [{"app_name": a} for a in pkg["apps"]],
                "modules": [{"module_name": m} for m in pkg["modules"]],
                "roles": [{"role": r} for r in pkg["roles"]],
            })
            doc.insert(ignore_permissions=True)

    frappe.db.commit()
