import frappe

def bootstrap_site(
    company_name,
    abbr,
    country="Saudi Arabia",
    currency="SAR",
    timezone="Asia/Riyadh",
):
    frappe.set_user("Administrator")

    ensure_warehouse_types()
    # 1️⃣ Create Company (if not exists)
    if not frappe.db.exists("Company", company_name):
        company = frappe.get_doc({
            "doctype": "Company",
            "company_name": company_name,
            "abbr": abbr,
            "country": country,
            "default_currency": currency,
        })
        company.insert()
    else:
        company = frappe.get_doc("Company", company_name)

    # 2️⃣ Set Global Defaults
    frappe.defaults.set_global_default("company", company.name)
    frappe.defaults.set_global_default("currency", currency)
    frappe.defaults.set_global_default("country", country)

    # 3️⃣ Create Fiscal Year
    fy_name = "FY-2026"
    if not frappe.db.exists("Fiscal Year", fy_name):
        frappe.get_doc({
            "doctype": "Fiscal Year",
            "year_start_date": "2026-01-01",
            "year_end_date": "2026-12-31",
            "year": fy_name,
            "companies": [{
                "company": company.name
            }]
        }).insert()

    # 4️⃣ Mark Setup Complete (CRITICAL)
    # frappe.db.set_single_value("System Settings", "setup_complete", 1)

    frappe.db.commit()

def ensure_warehouse_types():
    required_types = [
        "Stores",
        "Work In Progress",
        "Finished Goods",
        "Transit",
    ]

    for wt in required_types:
        if not frappe.db.exists("Warehouse Type", wt):
            frappe.get_doc({
                "doctype": "Warehouse Type",
                "name": wt,                  # ✅ REQUIRED
                "warehouse_type_name": wt,
            }).insert(ignore_permissions=True)
