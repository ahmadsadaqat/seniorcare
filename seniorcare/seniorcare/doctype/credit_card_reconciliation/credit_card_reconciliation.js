// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Credit Card Reconciliation", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Reconciled") {
			const approverRoles = ["Senior Care Approver", "Senior Care Manager", "System Manager"];
			const userRoles = frappe.user_roles || [];
			if (approverRoles.some(r => userRoles.includes(r))) {
				frm.add_custom_button(__("CEO / Approver Sign-off"), () => {
					frappe.prompt(
						[
							{
								fieldname: "notes",
								fieldtype: "Small Text",
								label: __("Sign-off Notes / Comments"),
							}
						],
						(values) => {
							frappe.call({
								method: "seniorcare.seniorcare.doctype.credit_card_reconciliation.credit_card_reconciliation.approve_credit_card_reconciliation",
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
						__("Reconciliation Sign-off"),
						__("Approve")
					);
				}).addClass("btn-primary");
			}
		}
	},

	calculate_totals(frm) {
		let total_stmt = 0.0;
		let total_matched = 0.0;
		let unmatched = 0;

		(frm.doc.statement_lines || []).forEach(row => {
			const amt = flt(row.amount);
			total_stmt += amt;
			if (row.match_status === "Matched" && row.matched_expense) {
				total_matched += amt;
			} else {
				unmatched += 1;
			}
		});

		frm.set_value("total_statement_amount", total_stmt);
		frm.set_value("total_matched_amount", total_matched);
		frm.set_value("unmatched_statement_lines", unmatched);
	}
});

frappe.ui.form.on("Credit Card Statement Line", {
	amount(frm) { frm.trigger("calculate_totals"); },
	match_status(frm) { frm.trigger("calculate_totals"); },
	matched_expense(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.matched_expense) {
			frappe.db.get_value("Credit Card Expense", row.matched_expense, ["amount", "description"])
				.then(r => {
					if (r && r.message) {
						if (!row.amount) frappe.model.set_value(cdt, cdn, "amount", r.message.amount);
						if (!row.description) frappe.model.set_value(cdt, cdn, "description", r.message.description);
						frappe.model.set_value(cdt, cdn, "match_status", "Matched");
					}
				});
		}
		frm.trigger("calculate_totals");
	},
	statement_lines_remove(frm) { frm.trigger("calculate_totals"); }
});
