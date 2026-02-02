// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

const PROVISION_STEPS = [
    "INIT",
    "SITE_CREATED",
    "APPS_INSTALLED",
    "BOOTSTRAPPED",
    "COMPLETED",
];

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

        // 🔒 New doc → no buttons
        if (frm.is_new()) return;

        if (frm.doc.status === "Provisioning") {
            frm.dashboard.clear_headline();
            frm.dashboard.set_headline(`
                <div style="display:flex; align-items:center; gap:10px;">
                    <img src="/assets/sowaan_cloud/images/provisioning_loader.gif" style="height:32px;">
                    <span>Provisioning in progress…</span>
                </div>
            `);            
            // show_provisioning_loader(frm);


        }


        // 🔒 Active or Provisioning → no button
        if (["Active", "Provisioning"].includes(frm.doc.status)) {
            return;
        }

        // ▶️ Create Instance button
        frm.add_custom_button(__("Create Instance"), () => {
            frappe.confirm(
                __("Start provisioning this instance?"),
                () => {
                    frappe.call({
                        method: "sowaan_cloud.utils.provision.create_instance",
                        args: {
                            docname: frm.doc.name,
                        },
                        freeze: true,
                        freeze_message: __("Provisioning started…"),
                        callback() {
                            frappe.show_alert({
                                message: __("Provisioning started"),
                                indicator: "blue",
                            });
                            frm.reload_doc();
                        },
                    });
                }
            );
        });

        // 🔵 Provisioning state
        if (frm.doc.status === "Provisioning") {
            const stepIndex = PROVISION_STEPS.indexOf(frm.doc.provisioning_step);
            const progress =
                stepIndex >= 0
                    ? Math.round(
                          ((stepIndex + 1) / PROVISION_STEPS.length) * 100
                      )
                    : 5;

            frm.page.set_indicator(__("Provisioning"), "blue");

            frm.dashboard.clear_headline();
            frm.dashboard.add_progress(
                __("Provisioning Progress"),
                progress,
                __("Step: {0}", [frm.doc.provisioning_step || "INIT"]),
                "blue"
            );

            if (!frm.__provision_timer) {
                frm.__provision_timer = setInterval(() => {
                    frm.reload_doc();
                }, 5000);
            }
        }

        // 🟢 Active
        if (frm.doc.status === "Active") {
            frm.page.set_indicator(__("Active"), "green");
            clearInterval(frm.__provision_timer);
            frm.__provision_timer = null;
        }

        // 🔴 Failed
        if (frm.doc.status === "Failed") {
            frm.page.set_indicator(__("Failed"), "red");
            clearInterval(frm.__provision_timer);
            frm.__provision_timer = null;
        }
    },

    instance_name(frm) {
        if (frm.doc.instance_name && frm.doc.your_site_name_suffix) {
            frm.set_value(
                "site_name",
                `${frm.doc.instance_name}.${frm.doc.your_site_name_suffix}`
            );
        }
    },

    selected_package(frm) {
        render_package_details(frm);
    },

    onload(frm) {
        if (frm.is_new() && !frm.doc.your_site_name_suffix) {
            frappe.call({
                method:
                    "sowaan_cloud.sowaan_cloud.doctype.cloud_subscription.cloud_subscription.get_default_site_suffix",
                callback(r) {
                    if (frm.is_new() && !frm.doc.your_site_name_suffix) {
                        frm.set_value("your_site_name_suffix", r.message);
                    }
                },
            });
        }
    },
});

function show_provisioning_loader(frm) {
    const loader_html = `
        <div style="text-align:center; padding:20px;">
            <img
                src="/assets/sowaan_cloud/images/provisioning_loader.gif"
                style="max-width:120px; margin-bottom:10px;"
            />
            <div class="text-muted">
                Provisioning in progress…<br>
                This may take a few minutes.
            </div>
        </div>
    `;

    frm.fields_dict.provisioning_loader.$wrapper.html(loader_html);
}

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
        `,
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
