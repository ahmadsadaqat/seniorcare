// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Care Plan", {
	related_assessment(frm) {
		// Fetch goals and interventions from the related assessment
		if (frm.doc.related_assessment) {
			frappe.db.get_doc("Resident Assessment", frm.doc.related_assessment).then(doc => {
				if (doc.care_plan_goals && !frm.doc.care_plan_goal) {
					frm.set_value("care_plan_goal", doc.care_plan_goals);
				}
				if (doc.care_plan_actions_interventions && !frm.doc.intervention_instruction) {
					frm.set_value("intervention_instruction", doc.care_plan_actions_interventions);
				}
				if (doc.resident_file && !frm.doc.resident_file) {
					frm.set_value("resident_file", doc.resident_file);
				}
			});
		}
	}
});
