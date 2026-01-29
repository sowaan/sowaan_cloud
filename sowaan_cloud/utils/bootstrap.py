import frappe

from datetime import date

from frappe.utils import validate_email_address

def bootstrap_site(
    company_name,
    abbr,
    country,
    currency,
    user_email=None,
):
    frappe.set_user("Administrator")

    company = phase_1_master_data(
        company_name, abbr, country, currency
    )

    phase_2_accounting(company, country)
    phase_3_users(company, user_email)
    phase_4_defaults(company, country, currency)
    phase_5_finalize()

    frappe.db.commit()

def phase_1_master_data(company_name, abbr, country, currency):
    ensure_warehouse_types()

    if not frappe.db.exists("Company", company_name):
        company = frappe.get_doc({
            "doctype": "Company",
            "company_name": company_name,
            "abbr": abbr,
            "country": country,
            "default_currency": currency,
        }).insert(ignore_permissions=True)
    else:
        company = frappe.get_doc("Company", company_name)

    ensure_chart_of_accounts(company, country)
    ensure_fiscal_year(company)

    return company

def phase_2_accounting(company, country):
    ensure_default_taxes(company, country)
    ensure_tax_categories(company, country)

def phase_3_users(company, user_email):
    ensure_default_business_user(company, email=user_email)

def phase_4_defaults(company, country, currency):
    frappe.defaults.set_global_default("company", company.name)
    frappe.defaults.set_global_default("currency", currency)
    frappe.defaults.set_global_default("country", country)

    frappe.defaults.set_user_default("company", company.name)

def phase_5_finalize():
    # DB flags
    frappe.db.set_single_value("System Settings", "setup_complete", 1)
    frappe.db.set_value(
        "DefaultValue",
        {"defkey": "setup_complete"},
        "defvalue",
        "1",
    )

    frappe.clear_cache()


# Utility functions

def get_user_email(company, provided_email=None):
    """
    Returns a safe email for user creation.
    If provided email is invalid, falls back to dummy.
    """

    if provided_email:
        provided_email = provided_email.strip().lower()

        try:
            validate_email_address(provided_email, throw=True)
            return provided_email
        except Exception:
            # Invalid email → fallback
            pass

    # Dummy fallback (always valid)
    return f"ops@{company.abbr.lower()}.local"

def ensure_default_business_user(company, email=None):
    user_email = get_user_email(company, email)

    if frappe.db.exists("User", user_email):
        user = frappe.get_doc("User", user_email)
    else:
        user = frappe.get_doc({
            "doctype": "User",
            "email": user_email,
            "first_name": "Operations",
            "last_name": "User",
            "enabled": 1,
            "send_welcome_email": 0,
            "new_password": frappe.generate_hash(length=12),
        }).insert(ignore_permissions=True)

    assign_roles(user)
    set_user_defaults(user, company)
    restrict_user_to_company(user, company)

    user.save(ignore_permissions=True)
    return user

def assign_roles(user):
    roles = [
        "Sales User",
        "Purchase User",
        "Accounts User",
        "Stock User",
        "Manufacturing User",
    ]

    existing = {r.role for r in user.roles}

    for role in roles:
        if role not in existing:
            user.append("roles", {"role": role})


def set_user_defaults(user, company):
    frappe.defaults.set_user_default(
        "company",
        company.name,
        user=user.name,
    )

def restrict_user_to_company(user, company):
    if frappe.db.exists(
        "User Permission",
        {
            "user": user.name,
            "allow": "Company",
            "for_value": company.name,
        },
    ):
        return

    frappe.get_doc({
        "doctype": "User Permission",
        "user": user.name,
        "allow": "Company",
        "for_value": company.name,
        "apply_to_all_doctypes": 1,
    }).insert(ignore_permissions=True)

def get_country_tax_categories(country):
    """
    Defines tax categories per country.
    Extend safely as needed.
    """

    categories = {
        "Saudi Arabia": [
            {
                "name": "Standard VAT",
                "description": "Standard VAT 15%",
                "rate": 15,
                "default": 1,
            },
            {
                "name": "Zero Rated",
                "description": "Zero-rated VAT",
                "rate": 0,
                "default": 0,
            },
            {
                "name": "Exempt",
                "description": "VAT Exempt",
                "rate": 0,
                "default": 0,
            },
        ],
        "United Arab Emirates": [
            {
                "name": "Standard VAT",
                "description": "Standard VAT 5%",
                "rate": 5,
                "default": 1,
            },
            {
                "name": "Zero Rated",
                "description": "Zero-rated VAT",
                "rate": 0,
                "default": 0,
            },
            {
                "name": "Exempt",
                "description": "VAT Exempt",
                "rate": 0,
                "default": 0,
            },
        ],
        "India": [
            {
                "name": "GST Standard",
                "description": "GST 18%",
                "rate": 18,
                "default": 1,
            },
            {
                "name": "GST Zero Rated",
                "description": "GST 0%",
                "rate": 0,
                "default": 0,
            },
        ],
    }

    return categories.get(country, [])

def ensure_tax_category(company, category):
    """
    Creates Tax Category if missing.
    """

    name = f"{category['name']} - {company.abbr}"

    if frappe.db.exists("Tax Category", name):
        return frappe.get_doc("Tax Category", name)

    doc = frappe.get_doc({
        "doctype": "Tax Category",
        "title": category["name"],
        "company": company.name,
        "is_default": category["default"],
    }).insert(ignore_permissions=True)

    return doc

def link_tax_category_to_templates(
    company,
    category,
    sales_template,
    purchase_template,
):
    """
    Links tax category with tax templates.
    """

    # Sales
    frappe.db.set_value(
        "Sales Taxes and Charges Template",
        sales_template.name,
        "tax_category",
        f"{category['name']} - {company.abbr}",
    )

    # Purchase
    frappe.db.set_value(
        "Purchase Taxes and Charges Template",
        purchase_template.name,
        "tax_category",
        f"{category['name']} - {company.abbr}",
    )

def ensure_tax_categories(company, country):
    categories = get_country_tax_categories(country)

    if not categories:
        return

    # Get existing tax templates
    sales_templates = frappe.get_all(
        "Sales Taxes and Charges Template",
        filters={"company": company.name},
        fields=["name", "title"],
    )

    purchase_templates = frappe.get_all(
        "Purchase Taxes and Charges Template",
        filters={"company": company.name},
        fields=["name", "title"],
    )

    for cat in categories:
        tax_category = ensure_tax_category(company, cat)

        # Match templates by rate or title
        for st in sales_templates:
            if str(cat["rate"]) in st.title:
                frappe.db.set_value(
                    "Sales Taxes and Charges Template",
                    st.name,
                    "tax_category",
                    tax_category.name,
                )

        for pt in purchase_templates:
            if str(cat["rate"]) in pt.title:
                frappe.db.set_value(
                    "Purchase Taxes and Charges Template",
                    pt.name,
                    "tax_category",
                    tax_category.name,
                )


def get_country_tax_profile(country):
    """
    Returns tax configuration per country.
    Extend this dict as needed.
    """

    profiles = {
        "Saudi Arabia": {
            "rate": 15,
            "tax_name": "VAT 15%",
            "account_name": "VAT 15%",
            "account_type": "Tax",
        },
        "United Arab Emirates": {
            "rate": 5,
            "tax_name": "VAT 5%",
            "account_name": "VAT 5%",
            "account_type": "Tax",
        },
        "India": {
            "rate": 18,
            "tax_name": "GST 18%",
            "account_name": "GST 18%",
            "account_type": "Tax",
        },
    }

    return profiles.get(country)

def ensure_tax_account(company, profile):
    """
    Creates tax account if missing.
    """

    if frappe.db.exists(
        "Account",
        {"company": company.name, "account_name": profile["account_name"]},
    ):
        return frappe.get_doc(
            "Account",
            {"company": company.name, "account_name": profile["account_name"]},
        )

    parent_account = frappe.db.get_value(
        "Account",
        {
            "company": company.name,
            "account_type": "Tax",
            "is_group": 1,
        },
        "name",
    )

    if not parent_account:
        # Fallback to root
        parent_account = frappe.db.get_value(
            "Account",
            {"company": company.name, "is_group": 1},
            "name",
        )

    account = frappe.get_doc({
        "doctype": "Account",
        "account_name": profile["account_name"],
        "company": company.name,
        "parent_account": parent_account,
        "account_type": profile["account_type"],
        "is_group": 0,
    }).insert(ignore_permissions=True)

    return account

def ensure_tax_template(company, profile, tax_account, charge_type):
    """
    charge_type: 'Sales Taxes and Charges Template'
                 'Purchase Taxes and Charges Template'
    """

    template_name = f"{profile['tax_name']} - {company.abbr}"

    if frappe.db.exists(charge_type, template_name):
        return

    doc = frappe.get_doc({
        "doctype": charge_type,
        "title": profile["tax_name"],
        "company": company.name,
        "is_default": 1,
        "taxes": [{
            "charge_type": "On Net Total",
            "account_head": tax_account.name,
            "rate": profile["rate"],
            "description": profile["tax_name"],
        }],
    })

    doc.insert(ignore_permissions=True)

def ensure_default_taxes(company, country):
    profile = get_country_tax_profile(country)

    if not profile:
        # Country has no predefined tax
        return

    tax_account = ensure_tax_account(company, profile)

    ensure_tax_template(
        company,
        profile,
        tax_account,
        "Sales Taxes and Charges Template",
    )

    ensure_tax_template(
        company,
        profile,
        tax_account,
        "Purchase Taxes and Charges Template",
    )

def get_current_fiscal_year_dates():
    today = date.today()

    start_date = date(today.year, 1, 1)
    end_date = date(today.year, 12, 31)

    fy_name = f"FY-{today.year}"

    return fy_name, start_date, end_date

def company_has_accounts(company):
    return frappe.db.exists("Account", {"company": company.name})

def ensure_fiscal_year(company):
    fy_name, start_date, end_date = get_current_fiscal_year_dates()

    if frappe.db.exists("Fiscal Year", fy_name):
        # Ensure company is linked
        fy = frappe.get_doc("Fiscal Year", fy_name)
        companies = [c.company for c in fy.companies]

        if company.name not in companies:
            fy.append("companies", {"company": company.name})
            fy.save(ignore_permissions=True)

        return fy

    # Create FY if missing
    fy = frappe.get_doc({
        "doctype": "Fiscal Year",
        "year": fy_name,
        "year_start_date": start_date,
        "year_end_date": end_date,
        "companies": [{"company": company.name}],
    }).insert(ignore_permissions=True)

    return fy


def ensure_chart_of_accounts(company, country):
    """
    Dynamically import Chart of Accounts based on country.
    Safe to call multiple times.
    """

    # Skip if accounts already exist
    if company_has_accounts(company):
        return

    try:
        from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import (
            import_chart_of_accounts,
            get_chart_of_accounts,
        )
    except ImportError:
        frappe.throw("Chart of Accounts importer not available")


    # Normalize country name
    country = country.strip()

    available_charts = get_chart_of_accounts()

    coa_country = None

    # 1️⃣ Exact match
    if country in available_charts:
        coa_country = country

    # 2️⃣ Partial / contains match (Saudi Arabia case)
    else:
        for chart in available_charts:
            if country.lower() in chart.lower():
                coa_country = chart
                break

    # 3️⃣ Fallback
    if not coa_country:
        coa_country = "Standard"


def set_defaults(company):
    frappe.defaults.set_user_default("company", company.name)
    frappe.defaults.set_global_default("company", company.name)


def mark_setup_complete():
    # Newer Frappe
    frappe.db.set_single_value("System Settings", "setup_complete", 1)

    # Older Frappe (CRITICAL)
    frappe.db.set_value(
        "DefaultValue",
        {"defkey": "setup_complete"},
        "defvalue",
        "1"
    )

    frappe.db.commit()
    frappe.clear_cache()




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
