/**
 * Qatar Gratuity — Employee Form JS
 * Adds a "Calculate Gratuity" button on the Employee doctype
 */

frappe.ui.form.on("Employee", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Calculate Qatar Gratuity"), function () {
                _show_gratuity_dialog(frm);
            }, __("Actions"));
        }
    }
});


function _show_gratuity_dialog(frm) {
    const d = new frappe.ui.Dialog({
        title  : __("Qatar Gratuity Calculator"),
        fields : [
            {
                fieldname : "to_date",
                fieldtype : "Date",
                label     : __("Calculation / Termination Date"),
                default   : frappe.datetime.get_today(),
                reqd      : 1,
            },
            {
                fieldname    : "use_company_policy",
                fieldtype    : "Check",
                label        : __("Use Company Policy (5 Years Minimum)"),
                default      : 1,
                description  : __("Uncheck to apply Qatar Labour Law minimum (1 year)"),
            },
        ],
        primary_action_label: __("Calculate"),
        primary_action(values) {
            d.hide();
            frappe.call({
                method  : "qatar_gratuity.utils.gratuity_calculator.calculate_qatar_gratuity",
                args    : {
                    employee           : frm.doc.name,
                    to_date            : values.to_date,
                    use_company_policy : values.use_company_policy,
                },
                freeze         : true,
                freeze_message : __("Calculating Gratuity..."),
                callback(r) {
                    if (r.message) {
                        _show_gratuity_result(frm, r.message);
                    }
                },
            });
        },
    });
    d.show();
}


function _show_gratuity_result(frm, data) {
    if (!data.eligible) {
        frappe.msgprint({
            title  : __("Not Eligible"),
            message: `
                <div class="alert alert-warning">
                    <strong>${__("Employee is NOT eligible for Gratuity")}</strong><br><br>
                    ${data.reason}
                </div>
                <table class="table table-bordered table-sm mt-3">
                    <tr><td>${__("Employee")}</td><td><b>${data.employee_name}</b></td></tr>
                    <tr><td>${__("Joining Date")}</td><td>${data.joining_date}</td></tr>
                    <tr><td>${__("Calculation Date")}</td><td>${data.to_date}</td></tr>
                    <tr><td>${__("Service")}</td><td>${data.service_display || data.service_years + " years"}</td></tr>
                    <tr><td>${__("Unpaid Leave Days")}</td><td>${data.unpaid_leave_days}</td></tr>
                </table>`,
            indicator: "orange",
        });
        return;
    }

    const currency = data.currency || "QAR";

    frappe.msgprint({
        title    : __("Qatar Gratuity Calculation"),
        message  : `
            <div class="alert alert-success mb-3">
                <h4 class="mb-1">${__("Gratuity Amount")}: 
                    <strong>${currency} ${frappe.format(data.gratuity_amount, {fieldtype:"Currency"})}</strong>
                </h4>
            </div>
            <table class="table table-bordered table-sm">
                <tr><td>${__("Employee")}</td>
                    <td><b>${data.employee_name}</b> (${data.employee})</td></tr>
                <tr><td>${__("Department")}</td><td>${data.department || "-"}</td></tr>
                <tr><td>${__("Joining Date")}</td><td>${data.joining_date}</td></tr>
                <tr><td>${__("Calculation Date")}</td><td>${data.to_date}</td></tr>
                <tr><td>${__("Total Service")}</td>
                    <td><b>${data.service_display}</b> (${data.service_years} yrs)</td></tr>
                <tr><td>${__("Unpaid Leave Deducted")}</td><td>${data.unpaid_leave_days} days</td></tr>
                <tr><td>${__("Basic Salary (Monthly)")}</td>
                    <td>${currency} ${frappe.format(data.basic_salary, {fieldtype:"Currency"})}</td></tr>
                <tr><td>${__("Daily Basic")}</td>
                    <td>${currency} ${data.daily_basic}</td></tr>
                <tr><td>${__("Gratuity Days/Year")}</td>
                    <td>${data.gratuity_days_per_yr} days</td></tr>
                <tr><td>${__("Per Year Gratuity")}</td>
                    <td>${currency} ${frappe.format(data.gratuity_per_year, {fieldtype:"Currency"})}</td></tr>
                <tr class="table-success">
                    <td><b>${__("Total Gratuity")}</b></td>
                    <td><b>${currency} ${frappe.format(data.gratuity_amount, {fieldtype:"Currency"})}</b></td></tr>
            </table>
            <div class="text-muted small mt-2">
                <b>${__("Formula")}:</b> ${data.formula}<br>
                <b>${__("Policy")}:</b> ${data.policy_used}
            </div>`,
        indicator: "green",
        wide     : true,
    });

    // Offer to create Gratuity Voucher
    setTimeout(() => {
        frappe.confirm(
            __("Do you want to create a Gratuity Voucher for this employee?"),
            () => {
                frappe.new_doc("Qatar Gratuity Voucher", {
                    employee         : frm.doc.name,
                    termination_date : data.to_date,
                });
            }
        );
    }, 300);
}
