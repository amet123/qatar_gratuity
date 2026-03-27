"""
Monthly Gratuity Accrual — Scheduled Task
Runs every month to accrue gratuity liability for all active employees.
"""

import frappe
from frappe.utils import nowdate, flt
from qatar_gratuity.utils.gratuity_calculator import (
    calculate_qatar_gratuity,
    MIN_SERVICE_YEARS_POLICY,
)


def monthly_gratuity_accrual():
    """
    For each active employee with >= 5 years service,
    calculate monthly gratuity accrual and post a Journal Entry.
    """
    active_employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "company"],
    )

    for emp in active_employees:
        try:
            result = calculate_qatar_gratuity(
                employee           = emp.name,
                to_date            = nowdate(),
                use_company_policy = True,
            )

            if not result.get("eligible"):
                continue

            # Monthly accrual = total gratuity / total months of service
            total_months = flt(result["service_years"]) * 12
            if total_months <= 0:
                continue

            monthly_accrual = flt(result["gratuity_amount"]) / total_months

            _post_accrual_entry(emp, monthly_accrual, result)

        except Exception as e:
            frappe.log_error(
                title   = f"Qatar Gratuity Accrual Error: {emp.name}",
                message = str(e),
            )


def _post_accrual_entry(emp, monthly_accrual, result):
    """Post monthly accrual Journal Entry."""
    company  = emp.company
    currency = frappe.db.get_value("Company", company, "default_currency") or "QAR"

    expense_account = frappe.db.get_value(
        "Account",
        {"account_name": ["like", "%Gratuity Expense%"], "company": company},
        "name",
    )
    payable_account = frappe.db.get_value(
        "Account",
        {"account_name": ["like", "%Gratuity Payable%"], "company": company},
        "name",
    )

    if not expense_account or not payable_account:
        return  # Accounts not configured — skip silently

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company      = company
    je.posting_date = nowdate()
    je.user_remark  = (
        f"Monthly Gratuity Accrual: {emp.employee_name} ({emp.name}) | "
        f"Service: {result['service_display']}"
    )

    je.append("accounts", {
        "account"                    : expense_account,
        "debit_in_account_currency"  : flt(monthly_accrual, 2),
        "party_type"                 : "Employee",
        "party"                      : emp.name,
    })
    je.append("accounts", {
        "account"                    : payable_account,
        "credit_in_account_currency" : flt(monthly_accrual, 2),
        "party_type"                 : "Employee",
        "party"                      : emp.name,
    })

    je.flags.ignore_permissions = True
    je.insert()
    je.submit()
