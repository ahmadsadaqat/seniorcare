// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resident File", {
	refresh(frm) {
		if (!frm.is_new()) {
			// Add quick action buttons for operational convenience
			frm.add_custom_button(__("Book Appointment"), () => {
				frappe.new_doc("Doctor Appointment", {
					resident_file: frm.doc.name,
					doctor: frm.doc.primary_doctor
				});
			}, __("Actions"));

			frm.add_custom_button(__("New Contract"), () => {
				frappe.new_doc("Resident Contract", {
					resident_file: frm.doc.name,
					customer: frm.doc.customer
				});
			}, __("Actions"));

			frm.add_custom_button(__("Record Incident"), () => {
				frappe.new_doc("Incident Report", {
					resident_file: frm.doc.name
				});
			}, __("Actions"));

			frm.add_custom_button(__("Record Advance"), () => {
				frappe.new_doc("Resident Advance", {
					resident_file: frm.doc.name,
					customer: frm.doc.customer
				});
			}, __("Actions"));
		}
	},
	first_name(frm) {
		frm.trigger("set_full_name");
	},
	last_name(frm) {
		frm.trigger("set_full_name");
	},
	set_full_name(frm) {
		if (frm.doc.first_name) {
			let name = frm.doc.first_name + (frm.doc.last_name ? " " + frm.doc.last_name : "");
			frm.set_value("full_name", name.trim());
		}
	}
});
