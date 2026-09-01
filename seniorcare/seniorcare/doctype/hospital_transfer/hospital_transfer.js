// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Hospital Transfer", {
	refresh(frm) {
		// Show discharge action button for submitted transfers
		if (frm.doc.docstatus === 1 && !frm.doc.discharge_datetime) {
			frm.add_custom_button(__("Record Discharge"), () => {
				frappe.prompt([
					{
						fieldname: "discharge_datetime",
						label: "Discharge Date/Time",
						fieldtype: "Datetime",
						reqd: 1,
						default: frappe.datetime.now_datetime()
					},
					{
						fieldname: "diagnosis_on_discharge",
						label: "Diagnosis on Discharge",
						fieldtype: "Text"
					},
					{
						fieldname: "hospital_stay_charges",
						label: "Hospital Stay Charges",
						fieldtype: "Currency"
					}
				], (values) => {
					frappe.call({
						method: "frappe.client.amend_and_submit",
						args: { doc: frm.doc },
						callback: () => {
							// Use amend_doc pattern - just set values on submitted doc
							frm.set_value("discharge_datetime", values.discharge_datetime);
							if (values.diagnosis_on_discharge) {
								frm.set_value("diagnosis_on_discharge", values.diagnosis_on_discharge);
							}
							if (values.hospital_stay_charges) {
								frm.set_value("hospital_stay_charges", values.hospital_stay_charges);
							}
							frm.set_value("status", "Discharged");
							frm.save("Update");
						}
					});
				}, __("Record Discharge"), __("Save"));
			}).addClass("btn-primary");
		}
	}
});
