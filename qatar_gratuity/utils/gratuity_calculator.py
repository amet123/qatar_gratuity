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
from frappe.utils import (
    date_diff, getdate, flt, cint, nowdate, add_months
)
from dateutil.relativedelta import relativedelta


# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
GRATUITY_DAYS_PER_YEAR   = 21        # Qatar Labour Law minimum
WORKING_DAYS_IN_MONTH    = 30        # Qatar standard
MIN_SERVICE_YEARS_LAW    = 1         # Qatar Labour Law Article 54
MIN_SERVICE_YEARS_POLICY = 5         # Company policy (your requirement)


# ─────────────────────────────────────────────
# MAIN CALCULATION FUNCTION
# ─────────────────────────────────────────────
@frappe.whitelist()
def calculate_qatar_gratuity(employee, to_date=None, use_company_policy=True):
    """
    Calculate gratuity for a Qatar-based employee.

    Args:
        employee       : Employee ID (e.g. "HR-EMP-00001")
        to_date        : Calculation end date (default: today)
        use_company_policy: True  = 5-year minimum eligibility
                           False = 1-year minimum (Labour Law)

    Returns:
        dict with gratuity details
    """
    to_date = getdate(to_date or nowdate())

    emp = frappe.get_doc("Employee", employee)

    # ── 1. Get joining date ──────────────────
    joining_date = getdate(emp.date_of_joining)
    if not joining_date:
        frappe.throw(_("Employee {0} has no Date of Joining set.").format(employee))

    # ── 2. Calculate actual service ──────────
    unpaid_leave_days = _get_unpaid_leave_days(employee, joining_date, to_date)
    total_days        = date_diff(to_date, joining_date)
    effective_days    = total_days - unpaid_leave_days

    # Convert to years + months + days
    service           = _days_to_ymd(effective_days)
    service_years_flt = flt(effective_days) / 365.0   # float for calculation

    # ── 3. Eligibility check ─────────────────
    min_years = MIN_SERVICE_YEARS_POLICY if use_company_policy else MIN_SERVICE_YEARS_LAW

    if service_years_flt < min_years:
        return {
            "eligible"         : False,
            "reason"           : _(
                "Employee has {0:.2f} years of service. "
                "Minimum required: {1} year(s) [{2}]."
            ).format(
                service_years_flt,
                min_years,
                _("Company Policy") if use_company_policy else _("Qatar Labour Law")
            ),
            "employee"         : employee,
            "employee_name"    : emp.employee_name,
            "joining_date"     : str(joining_date),
            "to_date"          : str(to_date),
            "service_years"    : round(service_years_flt, 4),
            "service_display"  : _format_service(service),
            "unpaid_leave_days": unpaid_leave_days,
            "gratuity_amount"  : 0.0,
        }

    # ── 4. Get Basic Salary ──────────────────
    basic_salary = _get_basic_salary(employee, to_date)
    if not basic_salary:
        frappe.throw(_(
            "No active Salary Structure Assignment found for {0}. "
            "Please assign a Salary Structure with a Basic Salary component."
        ).format(employee))

    # ── 5. Calculate gratuity ────────────────
    daily_basic      = flt(basic_salary) / WORKING_DAYS_IN_MONTH
    gratuity_per_year = daily_basic * GRATUITY_DAYS_PER_YEAR
    gratuity_amount  = gratuity_per_year * service_years_flt

    return {
        "eligible"            : True,
        "employee"            : employee,
        "employee_name"       : emp.employee_name,
        "department"          : emp.department,
        "designation"         : emp.designation,
        "joining_date"        : str(joining_date),
        "to_date"             : str(to_date),
        "service_years"       : round(service_years_flt, 4),
        "service_display"     : _format_service(service),
        "unpaid_leave_days"   : unpaid_leave_days,
        "basic_salary"        : flt(basic_salary, 2),
        "daily_basic"         : flt(daily_basic, 4),
        "gratuity_days_per_yr": GRATUITY_DAYS_PER_YEAR,
        "gratuity_per_year"   : flt(gratuity_per_year, 2),
        "gratuity_amount"     : flt(gratuity_amount, 2),
        "currency"            : _get_company_currency(emp.company),
        "policy_used"         : _("Company Policy (5 yrs)") if use_company_policy
                                else _("Qatar Labour Law (1 yr)"),
        "formula"             : (
            f"({basic_salary} / {WORKING_DAYS_IN_MONTH}) "
            f"× {GRATUITY_DAYS_PER_YEAR} days "
            f"× {round(service_years_flt, 4)} years"
            f" = {flt(gratuity_amount, 2)}"
        ),
    }


# ─────────────────────────────────────────────
# SALARY STRUCTURE — BASIC SALARY
# ─────────────────────────────────────────────
def _get_basic_salary(employee, on_date):
    """
    Get basic salary from the active Salary Structure Assignment.
    Looks for a Salary Component named 'Basic' or 'Basic Salary'.
    """
    # Step 1: Find active Salary Structure Assignment
    assignments = frappe.get_all(
        "Salary Structure Assignment",
        filters={
            "employee"   : employee,
            "from_date"  : ["<=", on_date],
            "docstatus"  : 1,
        },
        fields=["salary_structure", "base", "from_date"],
        order_by="from_date desc",
        limit=1,
    )

    if not assignments:
        return None

    assignment = assignments[0]

    # Step 2: Try to get Basic component from Salary Structure
    structure_name = assignment.salary_structure
    basic_amount   = _get_basic_from_structure(structure_name, employee, on_date)

    if basic_amount:
        return basic_amount

    # Fallback: use base (CTC) from assignment if Basic component not found
    return flt(assignment.base) or None


def _get_basic_from_structure(structure_name, employee, on_date):
    """
    Extract Basic component value from Salary Structure.
    Handles both fixed-amount and formula-based components.
    """
    basic_keywords = ["basic", "basic salary", "basic pay"]

    earnings = frappe.get_all(
        "Salary Detail",
        filters={
            "parent"    : structure_name,
            "parenttype": "Salary Structure",
            "parentfield": "earnings",
        },
        fields=["salary_component", "amount", "formula", "amount_based_on_formula"],
    )

    for row in earnings:
        comp_name = (row.salary_component or "").lower().strip()
        if any(kw in comp_name for kw in basic_keywords):
            if not row.amount_based_on_formula:
                return flt(row.amount)
            # Formula-based: try last Salary Slip
            return _get_basic_from_last_slip(employee, on_date)

    return None


def _get_basic_from_last_slip(employee, on_date):
    """Get Basic from last submitted salary slip."""
    slips = frappe.get_all(
        "Salary Slip",
        filters={
            "employee"  : employee,
            "docstatus" : 1,
            "end_date"  : ["<=", on_date],
        },
        fields=["name"],
        order_by="end_date desc",
        limit=1,
    )
    if not slips:
        return None

    slip_name = slips[0].name
    basics    = frappe.get_all(
        "Salary Detail",
        filters={
            "parent"         : slip_name,
            "parenttype"     : "Salary Slip",
            "parentfield"    : "earnings",
            "salary_component": ["like", "%basic%"],
        },
        fields=["amount"],
        limit=1,
    )
    return flt(basics[0].amount) if basics else None


# ─────────────────────────────────────────────
# UNPAID LEAVE DAYS
# ─────────────────────────────────────────────
def _get_unpaid_leave_days(employee, from_date, to_date):
    """Sum all approved unpaid leave days (Leave Without Pay)."""
    lwp_types = frappe.get_all(
        "Leave Type",
        filters={"is_lwp": 1},
        pluck="name",
    )
    if not lwp_types:
        return 0

    result = frappe.db.sql("""
        SELECT COALESCE(SUM(total_leave_days), 0) AS days
        FROM   `tabLeave Application`
        WHERE  employee       = %(employee)s
          AND  leave_type     IN %(lwp_types)s
          AND  status         = 'Approved'
          AND  docstatus      = 1
          AND  from_date     >= %(from_date)s
          AND  to_date       <= %(to_date)s
    """, {
        "employee"  : employee,
        "lwp_types" : lwp_types,
        "from_date" : from_date,
        "to_date"   : to_date,
    }, as_dict=True)

    return flt(result[0].days) if result else 0.0


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _days_to_ymd(days):
    """Convert total days into years/months/days dict."""
    years  = days // 365
    remain = days % 365
    months = remain // 30
    ddays  = remain % 30
    return {"years": int(years), "months": int(months), "days": int(ddays)}


def _format_service(s):
    parts = []
    if s["years"]:  parts.append(f"{s['years']} Year(s)")
    if s["months"]: parts.append(f"{s['months']} Month(s)")
    if s["days"]:   parts.append(f"{s['days']} Day(s)")
    return ", ".join(parts) or "0 Days"


def _get_company_currency(company):
    return frappe.db.get_value("Company", company, "default_currency") or "QAR"
