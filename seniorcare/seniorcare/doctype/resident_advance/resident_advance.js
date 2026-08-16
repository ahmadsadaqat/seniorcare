// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resident Advance", {
	amount(frm) {
		frm.trigger("calculate_remaining");
	},
	utilized_amount(frm) {
		frm.trigger("calculate_remaining");
	},
	calculate_remaining(frm) {
		let remaining = flt(frm.doc.amount) - flt(frm.doc.utilized_amount);
		frm.set_value("remaining_balance", remaining);
	}
});
