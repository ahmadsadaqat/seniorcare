// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Doctor Appointment", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.follow_up_required && frm.doc.next_appointment_date) {
			frm.add_custom_button(__("Schedule Follow-up Appointment"), () => {
				frappe.new_doc("Doctor Appointment", {
					resident_file: frm.doc.resident_file,
					doctor: frm.doc.doctor,
					appointment_date: frm.doc.next_appointment_date,
					appointment_time: frm.doc.next_appointment_time,
					appointment_type: frm.doc.next_appointment_type || "Follow-up"
				});
			});
		}
	}
});
