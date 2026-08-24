// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vaccination Log", {
	refresh(frm) {
		if (frm.doc.resident_file) {
			frm.add_custom_button(__("View Resident File"), () => {
				frappe.set_route("Form", "Resident File", frm.doc.resident_file);
			});
		}
	}
});
