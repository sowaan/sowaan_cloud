frappe.provide("frappe.setup");

frappe.setup.on("after_load", function () {
    frappe.setup.add_step({
        name: "zatca_basic_info",
        title: __("ZATCA Information"),
        fields: [
            {
                fieldname: "zatca_vat_registration_number",
                label: __("VAT / Tax Identification Number"),
                fieldtype: "Data",
                reqd: 1
            },
            {
                fieldname: "commercial_registration_number",
                label: __("Commercial Registration Number"),
                fieldtype: "Data",
                reqd: 1
            },
            {
                fieldname: "zatca_business_category",
                label: __("Business Activity Type"),
                fieldtype: "Select",
                options: [
                    "Retail",
                    "Wholesale",
                    "Services",
                    "Manufacturing",
                    "Other"
                ],
                reqd: 1
            },
            {
                fieldname: "zatca_contact_email",
                label: __("ZATCA Contact Email"),
                fieldtype: "Data",
                options: "Email",
                reqd: 1
            },
            {
                fieldname: "zatca_contact_mobile",
                label: __("ZATCA Contact Mobile"),
                fieldtype: "Data",
                reqd: 1
            }
        ]
    });
});
