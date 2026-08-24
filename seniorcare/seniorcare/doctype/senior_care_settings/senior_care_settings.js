// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Senior Care Settings", {
	company(frm) {
		if (frm.doc.company) {
			frm.set_query("security_deposit_liability_account", () => {
				return { filters: { company: frm.doc.company, is_group: 0 } };
			});
			frm.set_query("medical_advance_liability_account", () => {
				return { filters: { company: frm.doc.company, is_group: 0 } };
			});
			frm.set_query("personal_advance_liability_account", () => {
				return { filters: { company: frm.doc.company, is_group: 0 } };
			});
			frm.set_query("medical_expense_account", () => {
				return { filters: { company: frm.doc.company, is_group: 0 } };
			});
			frm.set_query("personal_expense_account", () => {
				return { filters: { company: frm.doc.company, is_group: 0 } };
			});
			frm.set_query("resident_income_account", () => {
				return { filters: { company: frm.doc.company, is_group: 0 } };
			});
		}
	}
});
