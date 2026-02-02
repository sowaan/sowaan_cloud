// Copyright (c) 2026, Sowaan
// Cloud Subscription Client Script

/* -------------------------------------------------- */
/* Provisioning Steps (single source of truth)        */
/* -------------------------------------------------- */
const PROVISION_STEPS = [
    { key: "INIT", label: "Creating Site" },
    { key: "SITE_CREATED", label: "Installing Apps" },
    { key: "APPS_INSTALLED", label: "Bootstrapping Company" },
    { key: "BOOTSTRAPPED", label: "Finalizing Setup (DNS/SSL)" },
    { key: "COMPLETED", label: "Done" },
];

/* -------------------------------------------------- */
/* Inject CSS once                                   */
/* -------------------------------------------------- */
if (!document.getElementById("provisioning-css")) {
    const style = document.createElement("style");
    style.id = "provisioning-css";
    style.innerHTML = `
        .step-spinner {
            width:14px;
            height:14px;
            border:2px solid #cfe2ff;
            border-top:2px solid #0d6efd;
            border-radius:50%;
            display:inline-block;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}

/* -------------------------------------------------- */
/* Form Controller                                   */
/* -------------------------------------------------- */
frappe.ui.form.on("Cloud Subscription", {
    refresh(frm) {
        render_package_details(frm);

        if (frm.is_new()) return;

        // 🟢 ACTIVE
        if (frm.doc.status === "Active") {
            frm.page.set_indicator(__("Active"), "green");
            clear_provision_timer(frm);
            return;
        }

        // 🔴 FAILED
        if (frm.doc.status === "Failed") {
            frm.page.set_indicator(__("Failed"), "red");
            clear_provision_timer(frm);
            return;
        }

        // 🔵 PROVISIONING
        if (frm.doc.status === "Provisioning") {
            frm.page.set_indicator(__("Provisioning"), "blue");
            show_provisioning_loader(frm);
            start_auto_refresh(frm);
            return;
        }

        // ➕ CREATE INSTANCE BUTTON
        frm.add_custom_button(__("Create Instance"), () => {
            frappe.confirm(
                __("Start provisioning this instance?"),
                () => {
                    frappe.call({
                        method: "sowaan_cloud.utils.provision.create_instance",
                        args: { docname: frm.doc.name },
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
    },

    selected_package(frm) {
        render_package_details(frm);
    },

    instance_name(frm) {
        if (frm.doc.instance_name && frm.doc.your_site_name_suffix) {
            frm.set_value(
                "site_name",
                `${frm.doc.instance_name}.${frm.doc.your_site_name_suffix}`
            );
        }
    },

    onload(frm) {
        if (frm.is_new() && !frm.doc.your_site_name_suffix) {
            frappe.call({
                method: "sowaan_cloud.sowaan_cloud.doctype.cloud_subscription.cloud_subscription.get_default_site_suffix",
                callback(r) {
                    if (r.message) {
                        frm.set_value("your_site_name_suffix", r.message);
                    }
                },
            });
        }
    },
});

/* -------------------------------------------------- */
/* Loader + Animated Steps                            */
/* -------------------------------------------------- */
function show_provisioning_loader(frm) {
    const wrapper = frm.fields_dict.provisioning_loader.$wrapper;
    wrapper.empty();

    // wrapper.html(`
    //     <div style="text-align:center; padding:20px;">
    //         <img
    //             src="/assets/sowaan_cloud/images/provisioning_loader.gif"
    //             style="max-width:90px; margin-bottom:10px;"
    //         />
    //         <div class="text-muted">
    //             Provisioning in progress…<br>
    //             Please do not close this page.
    //         </div>
    //     </div>
    // `);

    render_provisioning_steps(frm);
}

function render_provisioning_steps(frm) {
    const current = frm.doc.provisioning_step || "INIT";
    const currentIndex = PROVISION_STEPS.findIndex(s => s.key === current);

    let html = `<div style="max-width:420px; margin:15px auto;">`;

    PROVISION_STEPS.forEach((step, index) => {
        let icon = "○";
        let color = "#adb5bd";
        let weight = "normal";

        if (index < currentIndex) {
            icon = "✔";
            color = "#28a745";
        } else if (index === currentIndex) {
            icon = `<span class="step-spinner"></span>`;
            color = "#0d6efd";
            weight = "bold";
        }

        html += `
            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                padding:6px 0;
                color:${color};
                font-weight:${weight};
            ">
                <span style="width:18px; text-align:center;">${icon}</span>
                <span>${step.label}</span>
            </div>
        `;
    });

    html += `</div>`;
    frm.fields_dict.provisioning_loader.$wrapper.append(html);
}

/* -------------------------------------------------- */
/* Auto Refresh                                      */
/* -------------------------------------------------- */
function start_auto_refresh(frm) {
    if (!frm.__provision_timer) {
        frm.__provision_timer = setInterval(() => {
            frm.reload_doc();
        }, 5000);
    }
}

function clear_provision_timer(frm) {
    if (frm.__provision_timer) {
        clearInterval(frm.__provision_timer);
        frm.__provision_timer = null;
    }
}

/* -------------------------------------------------- */
/* Package Details Renderer                           */
/* -------------------------------------------------- */
function render_package_details(frm) {
    const packages = {
        ZATCA_STARTER: `
            <b>ZATCA Starter Package</b>
            <ul>
                <li>ZATCA Phase 2 onboarding</li>
                <li>B2B & B2C invoices</li>
                <li>KSA Chart of Accounts</li>
                <li>Single warehouse stock</li>
            </ul>
        `,
        ZATCA_RETAIL_POS: `
            <b>ZATCA Retail & POS</b>
            <ul>
                <li>Everything in Starter</li>
                <li>POS setup (single outlet)</li>
                <li>Live ZATCA clearance</li>
            </ul>
        `,
        ZATCA_COMPLETE_SME: `
            <b>ZATCA Complete SME</b>
            <ul>
                <li>Multi warehouse</li>
                <li>VAT, AR/AP</li>
                <li>Full accounting</li>
            </ul>
        `,
    };

    if (!frm.doc.selected_package) {
        frm.set_df_property(
            "package_details",
            "options",
            `<span class="text-muted">Select a package to view details</span>`
        );
        return;
    }

    frm.set_df_property(
        "package_details",
        "options",
        packages[frm.doc.selected_package]
    );
}
