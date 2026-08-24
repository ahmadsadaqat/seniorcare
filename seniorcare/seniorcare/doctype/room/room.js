// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Room", {
	refresh(frm) {
		if (frm.doc.current_resident) {
			frm.add_custom_button(__("View Resident File"), () => {
				frappe.set_route("Form", "Resident File", frm.doc.current_resident);
			});
		}
	}
});
