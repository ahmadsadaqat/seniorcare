// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payroll Entry", {
	refresh(frm) {
		if (frm.doc.payroll_type === "Outsourced Employees" && frm.doc.company) {
			frm.trigger("set_auto_payroll_payable_account");
		}

		if (frm.doc.docstatus === 1 && frm.doc.payroll_type === "Outsourced Employees") {
			frm.add_custom_button(__("Make Accrual Entry"), () => {
				frm.call({
					method: "make_accrual_jv_entry",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Creating Accrual Entry..."),
					callback: function (r) {
						frm.refresh();
						frappe.msgprint(__("Accrual Entry processed successfully."));
					}
				});
			}, __("Accounting"));

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
							frappe.msgprint(__("Created {0} Outsourced Payroll Summary document(s): {1}", [
								r.message.length,
								r.message.join(", ")
							]));
							frappe.set_route("List", "Outsourced Payroll Summary", { payroll_entry: frm.doc.name });
						} else {
							frappe.msgprint(__("No submitted outsourced salary slips found for this Payroll Entry or summaries already exist."));
						}
					}
				});
			}, __("Actions"));
		}
	},

	payroll_type(frm) {
		frm.trigger("set_auto_payroll_payable_account");
	},

	company(frm) {
		frm.trigger("set_auto_payroll_payable_account");
	},

	set_auto_payroll_payable_account(frm) {
		if (!frm.doc.company || !frm.doc.payroll_type) return;

		frappe.call({
			method: "seniorcare.payroll.get_payroll_payable_account_for_company",
			args: {
				company: frm.doc.company,
				payroll_type: frm.doc.payroll_type
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value("payroll_payable_account", r.message);
				}
			}
		});
	}
});
