// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resident Assessment", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Create Care Plan"), () => {
				frappe.new_doc("Care Plan", {
					resident_file: frm.doc.resident_file,
					related_assessment: frm.doc.name,
					care_plan_goal: frm.doc.care_plan_goals,
					intervention_instruction: frm.doc.care_plan_actions_interventions
				});
			}, __("Actions"));

			frm.add_custom_button(__("Create ADL Assessment"), () => {
				frappe.new_doc("ADL Assessment", {
					resident_file: frm.doc.resident_file,
					assessed_by: frm.doc.assessed_by
				});
			}, __("Actions"));
		}
	}
});
