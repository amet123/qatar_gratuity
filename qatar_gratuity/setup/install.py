import frappe


WORKSPACE_NAME = "Qatar Gratuity"
SHORTCUT_LABEL = "Qatar Gratuity Voucher"


def after_install():
    ensure_workspace()


def after_migrate():
    ensure_workspace()


def ensure_workspace():
    workspace_name = frappe.db.exists("Workspace", WORKSPACE_NAME)

    if workspace_name:
        workspace = frappe.get_doc("Workspace", workspace_name)
    else:
        workspace = frappe.new_doc("Workspace")
        workspace.name = WORKSPACE_NAME

    workspace.title = WORKSPACE_NAME
    workspace.label = WORKSPACE_NAME
    workspace.module = WORKSPACE_NAME
    workspace.icon = "octicon octicon-calculator"
    workspace.public = 1
    workspace.is_hidden = 0
    workspace.parent_page = "Home"
    workspace.content = workspace.content or "[]"

    _ensure_shortcut(workspace)
    _ensure_role(workspace, "HR Manager")
    _ensure_role(workspace, "HR User")

    if workspace_name:
        workspace.save(ignore_permissions=True)
    else:
        workspace.insert(ignore_permissions=True)

    frappe.clear_cache()


def _ensure_shortcut(workspace):
    for row in workspace.shortcuts or []:
        if row.link_to == SHORTCUT_LABEL:
            row.label = SHORTCUT_LABEL
            row.type = "DocType"
            row.doc_view = "List"
            return

    workspace.append(
        "shortcuts",
        {
            "type": "DocType",
            "label": SHORTCUT_LABEL,
            "link_to": SHORTCUT_LABEL,
            "doc_view": "List",
        },
    )


def _ensure_role(workspace, role):
    for row in workspace.roles or []:
        if row.role == role:
            return
    workspace.append("roles", {"role": role})
