// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Wound Assessment", {
	refresh(frm) {
		// Filter existing wound reference to same resident
		frm.set_query("existing_wound_reference", () => {
			return {
				filters: {
					resident_file: frm.doc.resident_file,
					docstatus: 1,
					wound_status: ["!=", "Healed"]
				}
			};
		});
	}
});
