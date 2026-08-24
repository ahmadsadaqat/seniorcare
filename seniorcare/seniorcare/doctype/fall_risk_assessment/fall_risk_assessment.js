// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fall Risk Assessment", {
	refresh(frm) {
		if (frm.doc.resident_file) {
			frm.add_custom_button(__("View Resident File"), () => {
				frappe.set_route("Form", "Resident File", frm.doc.resident_file);
			});
		}
	},
	history_of_falls(frm) {
		frm.trigger("calculate_score");
	},
	secondary_diagnosis(frm) {
		frm.trigger("calculate_score");
	},
	mobility_aid(frm) {
		frm.trigger("calculate_score");
	},
	gait_transfer(frm) {
		frm.trigger("calculate_score");
	},
	awareness_of_limitations(frm) {
		frm.trigger("calculate_score");
	},
	iv_therapy_medical_lines(frm) {
		frm.trigger("calculate_score");
	},
	calculate_score(frm) {
		let score = 0;
		if (frm.doc.history_of_falls) score += 25;
		if (frm.doc.secondary_diagnosis) score += 15;
		if (["Cane", "Walker"].includes(frm.doc.mobility_aid)) score += 15;
		else if (frm.doc.mobility_aid === "Wheelchair") score += 30;

		if (frm.doc.iv_therapy_medical_lines) score += 20;

		if (frm.doc.gait_transfer === "Weak") score += 10;
		else if (frm.doc.gait_transfer === "Impaired") score += 20;

		if (["Overestimates ability", "Forgets limitations"].includes(frm.doc.awareness_of_limitations)) score += 15;

		frm.set_value("calculated_score", score);
		if (score <= 24) {
			frm.set_value("risk_level", "Low");
		} else if (score <= 45) {
			frm.set_value("risk_level", "Moderate");
		} else {
			frm.set_value("risk_level", "High");
		}
	}
});
