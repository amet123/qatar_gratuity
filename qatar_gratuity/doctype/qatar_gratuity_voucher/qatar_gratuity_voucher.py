"""
Qatar Gratuity Voucher — DocType Controller
ERPNext 15 Custom DocType
"""

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate
from qatar_gratuity.utils.gratuity_calculator import calculate_qatar_benefits


class QatarGratuityVoucher(Document):

    def validate(self):
        result = calculate_qatar_benefits(
            employee=self.employee,
            to_date=self.termination_date or nowdate(),
            excluded_days=self.excluded_days
        )

        self.service_years = result.get("service_years")
        self.basic_salary = result.get("basic_salary")
        self.eligible = result.get("eligible")
        self.gratuity_amount = result.get("gratuity_amount")
        self.leave_salary_amount = result.get("leave_salary_amount")
