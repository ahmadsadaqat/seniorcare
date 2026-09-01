// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("ADL Assessment", {
	refresh(frm) {
		frm.trigger("calculate_score");
	},

	bathing: function(frm) { frm.trigger("calculate_score"); },
	dressing: function(frm) { frm.trigger("calculate_score"); },
	toileting: function(frm) { frm.trigger("calculate_score"); },
	transferring: function(frm) { frm.trigger("calculate_score"); },
	continence_adl: function(frm) { frm.trigger("calculate_score"); },
	feeding: function(frm) { frm.trigger("calculate_score"); },

	calculate_score(frm) {
		let score = 0;
		const fields = ["bathing", "dressing", "toileting", "transferring", "continence_adl", "feeding"];
		fields.forEach(f => {
			if (frm.doc[f] && frm.doc[f] !== "Independent") {
				score += 1;
			}
		});
		frm.set_value("total_adl_score", score);
	}
});
