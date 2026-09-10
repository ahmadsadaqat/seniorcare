// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Document Checklist", {
	template(frm) {
		if (frm.doc.template) {
			frappe.call({
				method: "seniorcare.seniorcare.doctype.employee_document_checklist.employee_document_checklist.load_template_items",
				args: { template_name: frm.doc.template },
				callback(r) {
					if (r.message && r.message.length > 0) {
						frm.clear_table("checklist_items");
						r.message.forEach(item => {
							const row = frm.add_child("checklist_items");
							Object.assign(row, item);
						});
						frm.refresh_field("checklist_items");
					}
				}
			});
		}
	}
});
