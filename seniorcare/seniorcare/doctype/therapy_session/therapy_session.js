// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Therapy Session", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.billing_status === "Unbilled" && frm.doc.attendance_status === "Completed") {
			frm.add_custom_button(__("Create Sales Invoice"), () => {
				frappe.call({
					method: "seniorcare.seniorcare.doctype.therapy_session.therapy_session.invoice_therapy_session",
					args: { session_name: frm.doc.name },
					freeze: true,
					callback(r) {
						if (!r.exc) {
							frm.reload_doc();
						}
					}
				});
			}).addClass("btn-primary");
		}
	},

	therapy_type(frm) {
		if (frm.doc.therapy_type) {
			frappe.db.get_value("Therapy Type", frm.doc.therapy_type, ["default_duration_minutes", "default_rate"])
				.then(r => {
					if (r && r.message) {
						if (!frm.doc.duration_minutes) {
							frm.set_value("duration_minutes", r.message.default_duration_minutes);
						}
						if (!frm.doc.rate && !frm.doc.therapy_package) {
							frm.set_value("rate", r.message.default_rate);
						}
					}
				});
		}
	},

	resident_file(frm) {
		if (frm.doc.resident_file) {
			frappe.db.get_value("Resident File", frm.doc.resident_file, "customer")
				.then(r => {
					if (r && r.message) {
						frm.set_value("customer", r.message.customer);
					}
				});
		}
	}
});
