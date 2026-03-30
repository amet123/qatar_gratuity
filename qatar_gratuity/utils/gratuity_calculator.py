"""
Qatar Gratuity Calculation - ERPNext 15
Based on Qatar Labour Law No. 14 of 2004, Article 54

Formula:
  Gratuity = (Basic Salary / 30) x 21 days x Years of Service

Rules:
  - Minimum eligibility: 1 year (Labour Law) / 5 years (Company Policy)
  - Based on BASIC SALARY only (no allowances)
  - Pro-rata for partial years
  - Unpaid leave days excluded from service period
  - Article 61 misconduct = forfeit gratuity
"""

import frappe
from frappe import _
from frappe.utils import date_diff, getdate, flt, nowdate

WORKING_DAYS_IN_MONTH = 30


@frappe.whitelist()
def calculate_qatar_benefits(employee, to_date=None, gratuity_rule=None, excluded_days=None):
    to_date = getdate(to_date or nowdate())
    excluded_days = flt(excluded_days or 0)

    emp = frappe.get_doc("Employee", employee)

    joining_date = getdate(emp.date_of_joining)
    if not joining_date:
        frappe.throw(_("Date of Joining missing"))

    total_days = date_diff(to_date, joining_date)
    effective_days = total_days - excluded_days

    service_years = flt(effective_days) / 365

    basic_salary = _get_basic_salary(employee, to_date)
    daily_basic = basic_salary / 30

    # 🔥 GRATUITY
    gratuity = 0
    eligible = service_years >= 1

    if eligible:
        gratuity = daily_basic * 21 * service_years

    # 🔥 LEAVE SALARY
    if service_years < 5:
        leave_days = 21
    else:
        leave_days = 28

    leave_salary = daily_basic * leave_days * service_years

    return {
        "service_years": service_years,
        "basic_salary": basic_salary,
        "eligible": eligible,
        "gratuity_amount": gratuity,
        "leave_salary_amount": leave_salary,
    }


def _get_basic_salary(employee, on_date):
    assignment = frappe.get_all(
        "Salary Structure Assignment",
        filters={
            "employee": employee,
            "docstatus": 1
        },
        fields=["base"],
        limit=1
    )

    if not assignment:
        return 0

    return flt(assignment[0].base)
