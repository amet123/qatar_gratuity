"""
Qatar Gratuity Voucher — DocType Controller
ERPNext 15 Custom DocType
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate

from qatar_gratuity.utils.gratuity_calculator import calculate_qatar_gratuity


class QatarGratuityVoucher(Document):

    def validate(self):
        self._calculate()
        self._validate_eligibility()

    def _calculate(self):
        result = calculate_qatar_gratuity(
            employee           = self.employee,
            to_date            = self.termination_date or nowdate(),
            use_company_policy = cint(self.use_company_policy),
        )
        self.eligible           = result.get("eligible", False)
        self.service_years      = result.get("service_years", 0)
        self.service_display    = result.get("service_display", "")
        self.basic_salary       = result.get("basic_salary", 0)
        self.unpaid_leave_days  = result.get("unpaid_leave_days", 0)
        self.gratuity_amount    = result.get("gratuity_amount", 0)
        self.calculation_note   = result.get("formula", "") or result.get("reason", "")

    def _validate_eligibility(self):
        if not self.eligible:
            frappe.throw(_(
                "Employee is NOT eligible for Gratuity.\n{0}"
            ).format(self.calculation_note))

    def on_submit(self):
        self._create_journal_entry()

    def _create_journal_entry(self):
        """Post accounting entry on submit."""
        company     = frappe.db.get_value("Employee", self.employee, "company")
        currency    = frappe.db.get_value("Company", company, "default_currency")

        # Accounts — adjust account names to match your Chart of Accounts
        gratuity_expense_account  = _get_account("Gratuity Expense", company)
        gratuity_payable_account  = _get_account("Gratuity Payable", company)

        if not gratuity_expense_account or not gratuity_payable_account:
            frappe.msgprint(_(
                "Gratuity accounts not found. Journal Entry not created. "
                "Please create 'Gratuity Expense' and 'Gratuity Payable' accounts."
            ), alert=True)
            return

        je = frappe.new_doc("Journal Entry")
        je.voucher_type   = "Journal Entry"
        je.company        = company
        je.posting_date   = self.termination_date or nowdate()
        je.user_remark    = f"Qatar Gratuity for {self.employee_name} ({self.employee})"

        je.append("accounts", {
            "account"      : gratuity_expense_account,
            "debit_in_account_currency": flt(self.gratuity_amount),
            "party_type"   : "Employee",
            "party"        : self.employee,
        })
        je.append("accounts", {
            "account"      : gratuity_payable_account,
            "credit_in_account_currency": flt(self.gratuity_amount),
            "party_type"   : "Employee",
            "party"        : self.employee,
        })

        je.insert(ignore_permissions=True)
        je.submit()

        frappe.db.set_value(self.doctype, self.name,
                            "journal_entry", je.name)
        frappe.msgprint(_(
            "Journal Entry {0} created for QAR {1:,.2f}"
        ).format(je.name, self.gratuity_amount))


def _get_account(account_type, company):
    """Find account by name pattern."""
    result = frappe.db.get_value(
        "Account",
        {"account_name": ["like", f"%{account_type}%"], "company": company},
        "name",
    )
    return result


from frappe.utils import cint
