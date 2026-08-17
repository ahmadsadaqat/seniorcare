// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payroll Entry", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && (frm.doc.payroll_type === "Outsourced Employees" || frm.doc.payroll_type === "All Employees")) {
			frm.add_custom_button(__("Create Outsourced Payroll Summary"), () => {
				frappe.call({
					method: "seniorcare.payroll.create_outsourced_payroll_summaries_for_payroll_entry",
					args: {
						payroll_entry_name: frm.doc.name
					},
					freeze: true,
					freeze_message: __("Creating Outsourced Payroll Summaries..."),
					callback: function (r) {
						if (r.message && r.message.length > 0) {
							frappe.msgprint(__("Created {0} Outsourced Payroll Summaries: {1}", [
								r.message.length,
								r.message.join(", ")
							]));
							frappe.set_route("List", "Outsourced Payroll Summary", { payroll_entry: frm.doc.name });
						} else {
							frappe.msgprint(__("No submitted outsourced salary slips found for this Payroll Entry or summaries already exist."));
						}
					}
				}, __("Create"));
			});
		}
	}
});
