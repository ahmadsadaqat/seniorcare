// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Doctor Appointment", {
	refresh(frm) {
		if (frm.doc.resident_file) {
			frm.add_custom_button(__("View Resident File"), () => {
				frappe.set_route("Form", "Resident File", frm.doc.resident_file);
			});

			if (frm.doc.docstatus === 0) {
				frm.add_custom_button(__("Load Current Medications"), () => {
					frappe.call({
						method: "seniorcare.seniorcare.doctype.doctor_appointment.doctor_appointment.get_resident_current_medications",
						args: { resident_file: frm.doc.resident_file },
						callback(r) {
							if (r.message && r.message.length) {
								frm.clear_table("medication_orders");
								r.message.forEach(row => {
									frm.add_child("medication_orders", row);
								});
								frm.refresh_field("medication_orders");
								frappe.show_alert({ message: __("Current medications loaded successfully."), indicator: "green" });
							} else {
								frappe.msgprint(__("No existing medications found on Resident File."));
							}
						}
					});
				}, __("Actions"));

				frm.add_custom_button(__("Record Vitals"), () => {
					frappe.new_doc("Vital Signs Log", {
						resident_file: frm.doc.resident_file
					});
				}, __("Actions"));

				frm.add_custom_button(__("Create Lab Record"), () => {
					frappe.new_doc("Lab Record", {
						resident_file: frm.doc.resident_file,
						ordered_by: frm.doc.doctor,
						test_date: frm.doc.appointment_date || frappe.datetime.get_today()
					});
				}, __("Actions"));
			}
		}

		if (frm.doc.docstatus === 1 && frm.doc.follow_up_required && frm.doc.next_appointment_date) {
			frm.add_custom_button(__("Schedule Follow-up Appointment"), () => {
				frappe.new_doc("Doctor Appointment", {
					resident_file: frm.doc.resident_file,
					doctor: frm.doc.doctor,
					appointment_date: frm.doc.next_appointment_date,
					appointment_time: frm.doc.next_appointment_time,
					appointment_type: frm.doc.next_appointment_type || "Follow-up",
					referred_by: "Doctor Referral"
				});
			});
		}
	},

	follow_up_required(frm) {
		if (frm.doc.follow_up_required && !frm.doc.referred_by) {
			frm.set_value("referred_by", "Doctor Referral");
		}
	}
});
