# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CloudSubscription(Document):
	pass

@frappe.whitelist()
def get_default_site_suffix():
    return frappe.db.get_single_value(
        "Cloud Settings",
        "site_suffix"
    )