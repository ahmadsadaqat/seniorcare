// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Petty Cash Reconciliation", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Pending Review") {
			const approverRoles = ["Senior Care Approver", "Senior Care Manager", "System Manager"];
			const userRoles = frappe.user_roles || [];
			if (approverRoles.some(r => userRoles.includes(r))) {
				frm.add_custom_button(__("Approve Reconciliation"), () => {
					frappe.prompt(
						[
							{
								fieldname: "notes",
								fieldtype: "Small Text",
								label: __("Spot Check & Audit Notes"),
							}
						],
						(values) => {
							frappe.call({
								method: "seniorcare.seniorcare.doctype.petty_cash_reconciliation.petty_cash_reconciliation.approve_petty_cash_reconciliation",
								args: {
									rec_name: frm.doc.name,
									notes: values.notes,
								},
								freeze: true,
								callback(r) {
									if (!r.exc) frm.reload_doc();
								}
							});
						},
						__("Audit & Approve"),
						__("Approve")
					);
				}).addClass("btn-primary");
			}
		}
	},

	custodian(frm) {
		if (frm.doc.custodian && !frm.doc.opening_balance) {
			frappe.call({
				method: "seniorcare.seniorcare.doctype.petty_cash_reconciliation.petty_cash_reconciliation.get_custodian_opening_balance",
				args: { custodian: frm.doc.custodian },
				callback(r) {
					if (r.message !== undefined) {
						frm.set_value("opening_balance", r.message);
						frm.trigger("calculate_balances");
					}
				}
			});
		}
	},

	opening_balance(frm) { frm.trigger("calculate_balances"); },
	funding_received(frm) { frm.trigger("calculate_balances"); },

	calculate_balances(frm) {
		let total_exp = 0.0;
		(frm.doc.expenses || []).forEach(row => {
			total_exp += flt(row.amount);
		});
		frm.set_value("total_expenditure", total_exp);
		const closing = flt(frm.doc.opening_balance) + flt(frm.doc.funding_received) - total_exp;
		frm.set_value("closing_balance", closing);
	}
});

frappe.ui.form.on("Petty Cash Expense Item", {
	amount(frm) { frm.trigger("calculate_balances"); },
	expenses_remove(frm) { frm.trigger("calculate_balances"); }
});
