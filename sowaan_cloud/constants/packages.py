PACKAGE_APPS = {
    "ZATCA_STARTER": [
        "erpnext",
        "zatca",
        "sowaan_cloud",
        "sowaanerp_subscription",
        "ksa_print_formats",
    ],

    "ZATCA_RETAIL_POS": [
        "erpnext",
        "zatca",
        "sowaan_cloud",
        "sowaanerp_subscription",
        "ksa_print_formats",
        "posawesome",
    ],

    "ZATCA_COMPLETE_SME": [
        "erpnext",
        "zatca",
        "sowaan_cloud",
        "sowaanerp_subscription",
        "ksa_print_formats",
        "posawesome",
        # future apps here
    ],
}

PACKAGE_FEATURES = {
    "ZATCA_STARTER": {
        "modules": [
            "Selling",
            "Buying",
            "Accounts",
            "Stock",
        ],
        "roles": [
            "Sales User",
            "Purchase User",
            "Accounts User",
            "Stock User",
        ],
    },

    "ZATCA_RETAIL_POS": {
        "modules": [
            "Selling",
            "Buying",
            "Accounts",
            "Stock",
            "POS",
        ],
        "roles": [
            "Sales User",
            "Purchase User",
            "Accounts User",
            "Stock User",
            "POS User",
        ],
    },

    "ZATCA_COMPLETE_SME": {
        "modules": [
            "Selling",
            "Buying",
            "Accounts",
            "Stock",
            "POS",
            "Assets",
            "Projects",
            "CRM",
        ],
        "roles": [
            "Sales User",
            "Purchase User",
            "Accounts User",
            "Stock User",
            "POS User",
            "Projects User",
            "CRM User",
        ],
    },
}
