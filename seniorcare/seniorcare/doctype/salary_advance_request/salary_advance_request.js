// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Advance Request", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Pending Approval") {
			const approverRoles = ["Senior Care Approver", "Senior Care Manager", "System Manager"];
			const userRoles = frappe.user_roles || [];
			if (approverRoles.some(r => userRoles.includes(r))) {
				frm.add_custom_button(__("Approve Advance"), () => {
					frappe.call({
						method: "seniorcare.seniorcare.doctype.salary_advance_request.salary_advance_request.approve_salary_advance",
						args: { req_name: frm.doc.name },
						freeze: true,
						callback(r) {
							if (!r.exc) frm.reload_doc();
						}
					});
				}).addClass("btn-primary");
			}
		}

		if (frm.doc.docstatus === 1 && frm.doc.status === "Approved") {
			const hrFinanceRoles = ["Senior Care HR", "Senior Care Finance", "System Manager"];
			const userRoles = frappe.user_roles || [];
			if (hrFinanceRoles.some(r => userRoles.includes(r))) {
				frm.add_custom_button(__("Record Disbursement"), () => {
					frappe.prompt(
						[
							{
								fieldname: "payment_entry",
								fieldtype: "Link",
								label: __("Payment Entry Ref"),
								options: "Payment Entry"
							}
						],
						(values) => {
							frappe.call({
								method: "seniorcare.seniorcare.doctype.salary_advance_request.salary_advance_request.mark_salary_advance_disbursed",
								args: {
									req_name: frm.doc.name,
									payment_entry: values.payment_entry
								},
								freeze: true,
								callback(r) {
									if (!r.exc) frm.reload_doc();
								}
							});
						},
						__("Disburse Salary Advance"),
						__("Confirm")
					);
				}).addClass("btn-success");
			}
		}
	}
});
