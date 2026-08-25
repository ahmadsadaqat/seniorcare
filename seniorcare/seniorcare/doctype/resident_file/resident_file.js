// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resident File", {
	setup(frm) {
		frm.trigger("prevent_auto_save_on_attach");
	},

	onload(frm) {
		frm.trigger("prevent_auto_save_on_attach");
	},

	refresh(frm) {
		frm.trigger("prevent_auto_save_on_attach");
		frm.trigger("setup_custom_buttons");
		frm.trigger("filter_room_field");
	},

	prevent_auto_save_on_attach(frm) {
		const attach_fields = ["resident_photo", "dnr_document", "medical_documents"];
		attach_fields.forEach(fieldname => {
			const field = frm.get_field(fieldname);
			if (field && !field._auto_save_overridden) {
				field._auto_save_overridden = true;
				const orig_on_upload_complete = field.on_upload_complete.bind(field);
				field.on_upload_complete = async function(attachment) {
					if (this.frm && this.frm.is_new()) {
						await this.parse_validate_and_set_in_model(attachment.file_url);
						this.set_value(attachment.file_url);
						if (this.frm.attachments) {
							this.frm.attachments.update_attachment(attachment);
						}
						this.refresh();
					} else {
						orig_on_upload_complete(attachment);
					}
				};
			}
		});
	},

	setup_custom_buttons(frm) {
		if (!frm.is_new()) {
			// Clinical & Medical Actions
			frm.add_custom_button(__("Book Appointment"), () => {
				frappe.new_doc("Doctor Appointment", {
					resident_file: frm.doc.name,
					doctor: frm.doc.primary_doctor
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Record Vitals"), () => {
				frappe.new_doc("Vital Signs Log", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Log Vaccination"), () => {
				frappe.new_doc("Vaccination Log", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Daily Health Log"), () => {
				frappe.new_doc("Daily Health Log", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Fall Risk Assessment"), () => {
				frappe.new_doc("Fall Risk Assessment", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Record Incident"), () => {
				frappe.new_doc("Incident Report", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Assign Attendant"), () => {
				const new_doc = frappe.model.get_new_doc("Attendant Assignment");
				frappe.set_route("Form", "Attendant Assignment", new_doc.name).then(() => {
					cur_frm.add_child("assigned_residents", {
						resident_file: frm.doc.name,
						resident_name: frm.doc.full_name,
						room_unit: frm.doc.room_unit,
						care_acuity_level: frm.doc.care_acuity_level
					});
					cur_frm.refresh_field("assigned_residents");
				});
			}, __("Actions"));

			// Financial & Commercial Actions
			frm.add_custom_button(__("New Contract"), () => {
				frappe.new_doc("Resident Contract", {
					resident_file: frm.doc.name,
					customer: frm.doc.customer
				});
			}, __("Financial Actions"));

			frm.add_custom_button(__("Refresh Financial Balances"), () => {
				frappe.call({
					method: "seniorcare.seniorcare.doctype.resident_file.resident_file.refresh_resident_financials",
					args: { resident_file: frm.doc.name },
					callback(r) {
						if (r.message) {
							frm.reload_doc();
							frappe.show_alert({ message: __("Financial balances updated from Payment Entries."), indicator: "green" });
						}
					}
				});
			}, __("Financial Actions"));

			frm.add_custom_button(__("Generate Monthly Invoice"), () => {
				frappe.call({
					method: "seniorcare.billing.generate_resident_invoice",
					args: { resident_file: frm.doc.name },
					callback(r) {
						if (r.message) {
							frappe.show_alert({ message: __("Draft Sales Invoice {0} created.", [r.message]), indicator: "green" });
							frappe.set_route("Form", "Sales Invoice", r.message);
						}
					}
				});
			}, __("Financial Actions"));
		}
	},

	filter_room_field(frm) {
		frm.set_query("room_unit", () => {
			return {
				filters: [
					["Room", "occupancy_status", "in", ["Available", "Reserved"]],
				]
			};
		});
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
	},

	date_of_birth(frm) {
		if (frm.doc.date_of_birth) {
			let dob = new Date(frm.doc.date_of_birth);
			let today = new Date();
			let age = today.getFullYear() - dob.getFullYear();
			let m = today.getMonth() - dob.getMonth();
			if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
				age--;
			}
			frm.set_value("age", Math.max(0, age));
		}
	}
});
