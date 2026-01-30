import frappe # type: ignore
from datetime import date
from frappe.utils import validate_email_address # type: ignore

from frappe.desk.page.setup_wizard.setup_wizard import setup_complete # type: ignore
from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import ( # type: ignore
    get_charts_for_country,
)

from erpnext.setup.setup_wizard.operations.taxes_setup import setup_taxes_and_charges # type: ignore

DEFAULT_PASSWORD = "Abc@12345"


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------

def bootstrap_site(company_name, abbr, country, currency, user_email=None):
    """
    Full headless bootstrap for a new ERPNext site.
    """

    frappe.set_user("Administrator")

    company = run_setup_wizard(
        company_name=company_name,
        abbr=abbr,
        country=country,
        currency=currency,
        user_email=user_email,
    )

    # Post-setup customization only
    ensure_default_business_user(company, user_email)
    ensure_warehouse_types()
    setup_taxes_and_charges(company_name, country)

    ensure_default_taxes(company, country)

    ensure_tax_categories(company, country)
    # ensure_item_tax_templates(company, country)  # NEW
    frappe.db.commit()


# ------------------------------------------------------------
# Setup Wizard (single source of truth)
# ------------------------------------------------------------

def run_setup_wizard(company_name, abbr, country, currency, user_email):
    """
    Executes ERPNext Setup Wizard programmatically.
    This creates:
    - Company
    - COA
    - Fiscal Year
    - Default taxes & accounts
    """

    if frappe.db.exists("Company", company_name):
        return frappe.get_doc("Company", company_name)

    start_date, end_date = get_current_fiscal_year_dates()
    coa = pick_country_coa(country)

    args = {
        "company_name": company_name,
        "company_abbr": abbr,
        "country": country,
        "currency": currency,
        "chart_of_accounts": coa,
        "timezone": "Asia/Riyadh",
        "language": "english",
        "email": user_email or "admin@example.com",
        "full_name": "Operations User",
        "password": DEFAULT_PASSWORD,
        "fy_start_date": start_date,
        "fy_end_date": end_date,
    }

    frappe.logger("provisioning").info(
        f"Running setup_complete for {company_name} using COA: {coa}"
    )

    setup_complete(args)

    return frappe.get_doc("Company", company_name)


# ------------------------------------------------------------
# Chart of Accounts selection
# ------------------------------------------------------------

def pick_country_coa(country):
    """
    Pick the most appropriate COA for a country.

    Priority:
    1) Exact country-specific COA
    2) Standard with Numbers
    3) Standard
    """

    charts = get_charts_for_country(country, with_standard=False)

    frappe.logger("provisioning").info(
        f"Country-specific COAs for '{country}': {charts}"
    )

    if len(charts) == 1:
        return charts[0]

    for chart in charts:
        if country.lower() in chart.lower():
            return chart

    charts = get_charts_for_country(country, with_standard=True)
    if "Standard with Numbers" in charts:
        return "Standard with Numbers"

    return "Standard"


# ------------------------------------------------------------
# Users
# ------------------------------------------------------------

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
            "new_password": DEFAULT_PASSWORD,
        }).insert(ignore_permissions=True)

    assign_roles(user)
    set_user_defaults(user, company)
    restrict_user_to_company(user, company)

    user.save(ignore_permissions=True)
    return user


def get_user_email(company, provided_email=None):
    if provided_email:
        try:
            validate_email_address(provided_email.strip().lower(), throw=True)
            return provided_email.strip().lower()
        except Exception:
            pass

    return f"ops@{company.abbr.lower()}.local"


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
    frappe.defaults.set_user_default("company", company.name, user=user.name)


def restrict_user_to_company(user, company):
    if frappe.db.exists(
        "User Permission",
        {"user": user.name, "allow": "Company", "for_value": company.name},
    ):
        return

    frappe.get_doc({
        "doctype": "User Permission",
        "user": user.name,
        "allow": "Company",
        "for_value": company.name,
        "apply_to_all_doctypes": 1,
    }).insert(ignore_permissions=True)


# ------------------------------------------------------------
# Warehouses
# ------------------------------------------------------------

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
                "name": wt,
                "warehouse_type_name": wt,
            }).insert(ignore_permissions=True)


# ------------------------------------------------------------
# Dates
# ------------------------------------------------------------

def get_current_fiscal_year_dates():
    today = date.today()
    return date(today.year, 1, 1), date(today.year, 12, 31)

#------------------------------------------------------------
# TAXES RELATED FUNCTIONS
#------------------------------------------------------------
def has_default_taxes(company):
    return (
        frappe.db.exists(
            "Sales Taxes and Charges Template",
            {"company": company.name}
        )
        or frappe.db.exists(
            "Purchase Taxes and Charges Template",
            {"company": company.name}
        )
    )

def ensure_default_taxes(company, country):
    """
    Ensure country-specific taxes exist.
    ERPNext-first, custom fallback second.
    """

    # 1️⃣ Let ERPNext win if it already created taxes
    if has_default_taxes(company):
        return

    # 2️⃣ Otherwise, fallback to custom profiles
    profile = get_country_tax_profile(country)
    if not profile:
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

def get_country_tax_profile(country):
    profiles = {
        "Saudi Arabia": {
            "rate": 15,
            "tax_name": "VAT 15%",
            "account_name": "VAT 15%",
            "account_type": "Tax",
        },

    }
    return profiles.get(country)

#------------------------------------------------------------
# TAX CATEGORIES
#------------------------------------------------------------

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

def template_has_rate(template_name, rate, child_doctype):
    taxes = frappe.get_all(
        child_doctype,
        filters={"parent": template_name},
        fields=["rate"],
    )
    return any(float(t.rate) == float(rate) for t in taxes)

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
            if template_has_rate(st.name, cat["rate"], "Sales Taxes and Charges"):
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


#------------------------------------------------------------
# ITEM TAX TEMPLATES
#------------------------------------------------------------

def get_country_item_tax_profiles(country):
    return {
        "Saudi Arabia": [
            {
                "name": "Standard VAT",
                "rate": 15,
                "tax_category": "Standard VAT",
                "default": 1,
            },
            {
                "name": "Zero Rated VAT",
                "rate": 0,
                "tax_category": "Zero Rated",
                "default": 0,
            },
            {
                "name": "Exempt VAT",
                "rate": 0,
                "tax_category": "Exempt",
                "default": 0,
            },
        ]
    }.get(country, [])

def find_tax_template_by_rate(company, rate, template_doctype, child_doctype):
    templates = frappe.get_all(
        template_doctype,
        filters={"company": company.name},
        fields=["name"],
    )

    for t in templates:
        if template_has_rate(t.name, rate, child_doctype):
            return t.name

    return None

def ensure_item_tax_template(company, profile):
    name = f"{profile['name']} - {company.abbr}"

    if frappe.db.exists("Item Tax Template", name):
        return

    sales_tax = find_tax_template_by_rate(
        company, profile["rate"],
        "Sales Taxes and Charges Template",
        "Sales Taxes and Charges",
    )

    purchase_tax = find_tax_template_by_rate(
        company, profile["rate"],
        "Purchase Taxes and Charges Template",
        "Purchase Taxes and Charges",
    )

    if not sales_tax and not purchase_tax:
        return

    doc = frappe.get_doc({
        "doctype": "Item Tax Template",
        "name": name,
        "company": company.name,
        "is_default": profile.get("default", 0),
        "tax_category": f"{profile['tax_category']} - {company.abbr}",
        "taxes": [],
    })

    if sales_tax:
        doc.append("taxes", {"tax_type": sales_tax})

    if purchase_tax:
        doc.append("taxes", {"tax_type": purchase_tax})

    doc.insert(ignore_permissions=True)


def find_tax_template_by_rate(company, rate, template_doctype, child_doctype):
    templates = frappe.get_all(
        template_doctype,
        filters={"company": company.name},
        fields=["name"],
    )

    for t in templates:
        if template_has_rate(t.name, rate, child_doctype):
            return t.name

    return None


def ensure_item_tax_template(company, profile):
    template_name = f"{profile['tax_name']} - {company.abbr}"

    # 1️⃣ If template already exists → DO NOTHING
    if frappe.db.exists("Item Tax Template", template_name):
        return

    tax_account = frappe.db.get_value(
        "Account",
        {
            "company": company.name,
            "account_name": profile["account_name"],
        },
        "name",
    )

    if not tax_account:
        return  # safety

    doc = frappe.get_doc({
        "doctype": "Item Tax Template",
        "name": template_name,
        "company": company.name,
        "taxes": [
            {
                "tax_type": tax_account,
                "tax_rate": profile["rate"],
            }
        ],
    })

    doc.insert(ignore_permissions=True)


def ensure_item_tax_templates(company, country):
    profile = get_country_tax_profile(country)
    if not profile:
        return

    ensure_item_tax_template(company, profile)
