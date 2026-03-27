from frappe import _


def get_data():
    return [
        {
            "module_name": "Qatar Gratuity",
            "category": "Modules",
            "label": _("Qatar Gratuity"),
            "color": "blue",
            "icon": "octicon octicon-calculator",
            "type": "module",
            "description": _("Qatar gratuity calculations and voucher management."),
        }
    ]
