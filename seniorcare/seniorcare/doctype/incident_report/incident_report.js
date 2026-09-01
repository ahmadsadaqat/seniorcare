// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Incident Report", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Initiate Hospital Transfer"), () => {
				frappe.new_doc("Hospital Transfer", {
					resident_file: frm.doc.resident_file,
					related_incident: frm.doc.name,
					reason: `Transfer initiated from Incident Report ${frm.doc.name}: ${frm.doc.incident_type} - ${(frm.doc.description || "").substring(0, 200)}`
				});
			}, __("Actions"));
		}
	}
});
