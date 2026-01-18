import frappe

def setup_wizard_save_zatca_info(args):
    company_name = args.get("company")
    if not company_name:
        return

    company = frappe.get_doc("Company", company_name)

    company.zatca_vat_registration_number = args.get("zatca_vat_registration_number")
    company.commercial_registration_number = args.get("commercial_registration_number")
    company.zatca_business_category = args.get("zatca_business_category")
    company.zatca_contact_email = args.get("zatca_contact_email")
    company.zatca_contact_mobile = args.get("zatca_contact_mobile")

    # Explicitly mark status
    company.zatca_status = "Not Registered"

    company.save(ignore_permissions=True)
