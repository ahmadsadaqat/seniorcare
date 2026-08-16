// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resident Contract", {
	refresh(frm) {
		// Calculate total monthly fee live
	},
	occupancy_fee(frm) {
		frm.trigger("calculate_totals");
	},
	attendant_fee(frm) {
		frm.trigger("calculate_totals");
	},
	other_fixed_charges(frm) {
		frm.trigger("calculate_totals");
	},
	calculate_totals(frm) {
		let total = flt(frm.doc.occupancy_fee) + flt(frm.doc.attendant_fee) + flt(frm.doc.other_fixed_charges);
		frm.set_value("total_monthly_fee", total);
	}
});
