import frappe


WORKSPACE_NAME = "Qatar Gratuity"


def after_install():
    ensure_workspace()


def after_migrate():
    ensure_workspace()


def ensure_workspace():
    if frappe.db.exists("Workspace", WORKSPACE_NAME):
        return

    workspace = frappe.get_doc(
        {
            "doctype": "Workspace",
            "name": WORKSPACE_NAME,
            "title": WORKSPACE_NAME,
            "label": WORKSPACE_NAME,
            "module": WORKSPACE_NAME,
            "public": 1,
            "icon": "octicon octicon-calculator",
            "content": "[]",
        }
    )
    workspace.append(
        "shortcuts",
        {
            "type": "DocType",
            "label": "Qatar Gratuity Voucher",
            "link_to": "Qatar Gratuity Voucher",
            "doc_view": "List",
        },
    )
    workspace.append("roles", {"role": "HR Manager"})
    workspace.append("roles", {"role": "HR User"})
    workspace.insert(ignore_permissions=True)
