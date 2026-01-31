// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cloud Subscription", {
    refresh(frm) {
        render_package_details(frm);
        if (!frm.doc.selected_package) {
            frm.set_df_property(
                "package_details",
                "options",
                `<span class="text-muted">
                Please select a package to view details.
            </span>`
            );
        }

        if (!frm.doc.instance_created && !frm.is_new()) {
            frm.add_custom_button(
                __("Create Instance"),
                () => {
                    frappe.call({
                        method: "sowaan_cloud.utils.provision.create_instance",
                        args: { docname: frm.doc.name },
                    });
                }
            );
        }
    },
    instance_name(frm) {
        if (frm.doc.instance_name) {
            // frm.set_df_property(
            //     "site_link",
            //     "options",
            //     `Click Here <a href="https://${frm.doc.instance_name}.${frm.doc.your_site_name_suffix}" target="_blank">
            //         ${frm.doc.instance_name}.${frm.doc.your_site_name_suffix}
            //     </a>`
            // );
            
            frm.set_value("site_name", `${frm.doc.instance_name}.${frm.doc.your_site_name_suffix}`);
        }
    },
    selected_package(frm) {
        render_package_details(frm);
    },
    onload(frm) {
        // Only for NEW documents
        if (frm.is_new() && !frm.doc.your_site_name_suffix) {
            frappe.call({
                method: "sowaan_cloud.sowaan_cloud.doctype.cloud_subscription.cloud_subscription.get_default_site_suffix",
                callback(r) {
                    if (frm.is_new() && !frm.doc.your_site_name_suffix) {
                        frm.set_value("your_site_name_suffix", r.message);
                    }
                }
            });

        }
    }    
});
function render_package_details(frm) {
    const packages = {
        ZATCA_STARTER: `
            <b>ZATCA Starter Package</b><br>
            <ul>
                <li>Company, branch & fiscal year setup</li>
                <li>ZATCA Phase 2 onboarding (CSR, CSID)</li>
                <li>B2C & B2B invoices</li>
                <li>KSA Chart of Accounts (SME)</li>
                <li>Basic stock (single warehouse)</li>
            </ul>
            <b>Implementation:</b> ~8 hours<br>
            <b>Mode:</b> Wizard-based
        `,
        ZATCA_RETAIL_POS: `
            <b>ZATCA Retail & POS Package</b><br>
            <ul>
                <li>Everything in Starter</li>
                <li>POS configuration (single outlet)</li>
                <li>Real-time clearance / reporting</li>
                <li>POS stock & accounting integration</li>
            </ul>
            <b>Implementation:</b> ~16 hours<br>
            <b>Mode:</b> Guided POS + ZATCA wizard
        `,
        ZATCA_COMPLETE_SME: `
            <b>ZATCA Complete SME Package</b><br>
            <ul>
                <li>Everything in Retail & POS</li>
                <li>Multi-warehouse stock</li>
                <li>AR / AP / VAT</li>
                <li>ZATCA monitoring dashboard</li>
                <li>Full financial statements</li>
            </ul>
            <b>Implementation:</b> Extended rollout
        `
    };

    if (!frm.doc.selected_package) {
        frm.set_df_property(
            "package_details",
            "options",
            `<span class="text-muted">
                Please select a package to view details.
            </span>`
        );
        return;
    }

    frm.set_df_property(
        "package_details",
        "options",
        packages[frm.doc.selected_package]
    );
}