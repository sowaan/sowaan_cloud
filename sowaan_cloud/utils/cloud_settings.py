import frappe

def get_cloud_settings():
    return frappe.get_single("Cloud Settings")