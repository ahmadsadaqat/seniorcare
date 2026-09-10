// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Petty Cash Fund", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Pending Approval") {
			const approverRoles = ["Senior Care Approver", "Senior Care Manager", "System Manager"];
			const userRoles = frappe.user_roles || [];
			if (approverRoles.some(r => userRoles.includes(r))) {
				frm.add_custom_button(__("Approve Funding"), () => {
					frappe.call({
						method: "seniorcare.seniorcare.doctype.petty_cash_fund.petty_cash_fund.approve_petty_cash_fund",
						args: { fund_name: frm.doc.name },
						freeze: true,
						callback(r) {
							if (!r.exc) frm.reload_doc();
						}
					});
				}).addClass("btn-primary");
			}
		}

		if (frm.doc.docstatus === 1 && frm.doc.status === "Approved") {
			const financeRoles = ["Senior Care Finance", "System Manager"];
			const userRoles = frappe.user_roles || [];
			if (financeRoles.some(r => userRoles.includes(r))) {
				frm.add_custom_button(__("Mark as Funded"), () => {
					frappe.prompt(
						[
							{
								fieldname: "bank_ref",
								fieldtype: "Data",
								label: __("Bank Transaction / Cheque Ref"),
								reqd: 1
							},
							{
								fieldname: "payment_entry",
								fieldtype: "Link",
								label: __("Payment Entry"),
								options: "Payment Entry"
							}
						],
						(values) => {
							frappe.call({
								method: "seniorcare.seniorcare.doctype.petty_cash_fund.petty_cash_fund.mark_fund_disbursed",
								args: {
									fund_name: frm.doc.name,
									bank_ref: values.bank_ref,
									payment_entry: values.payment_entry
								},
								freeze: true,
								callback(r) {
									if (!r.exc) frm.reload_doc();
								}
							});
						},
						__("Record Fund Disbursement"),
						__("Confirm Funded")
					);
				}).addClass("btn-success");
			}
		}
	}
});
