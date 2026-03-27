app_name = "qatar_gratuity"
app_title = "Qatar Gratuity"
app_publisher = "Your Company"
app_description = "Qatar Labour Law Gratuity Calculation for ERPNext 15"
app_version = "1.0.0"

# Doctype JS
doctype_js = {
    "Employee": "public/js/employee_gratuity.js"
}

# Scheduled Tasks
scheduler_events = {
    "monthly": [
        "qatar_gratuity.utils.gratuity_accrual.monthly_gratuity_accrual"
    ]
}
