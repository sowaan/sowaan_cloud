import frappe # type: ignore
import base64

@frappe.whitelist()
def get_file_content(file_url):
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    content = file_doc.get_content()
    return {
        "file_name": file_doc.file_name,
        "content_b64": base64.b64encode(content).decode(),
        "is_private": file_doc.is_private,
    }
