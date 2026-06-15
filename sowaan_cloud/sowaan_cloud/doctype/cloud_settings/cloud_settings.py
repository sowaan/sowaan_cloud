# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CloudSettings(Document):
	pass


@frappe.whitelist(allow_guest=True)
def get_site_suffix():
	try:
		suffix = frappe.db.get_single_value("Cloud Settings", "site_suffix")
		return suffix or "sowaan.cloud"
	except Exception:
		return "sowaan.cloud"
