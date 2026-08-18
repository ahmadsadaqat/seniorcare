// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Slip", {
	refresh(frm) {
		frm.trigger("sync_outsourced_fields");
	},

	employee(frm) {
		frm.trigger("sync_outsourced_fields");
	},

	sync_outsourced_fields(frm) {
		if (!frm.doc.employee) return;

		frappe.db.get_value(
			"Employee",
			frm.doc.employee,
			["is_outsourced_employee", "manpower_supplier", "vendor_employee_id"],
			(r) => {
				if (r && r.is_outsourced_employee) {
					frm.set_value("is_outsourced_employee", 1);
					frm.set_value("manpower_supplier", r.manpower_supplier);
					frm.set_value("vendor_employee_id", r.vendor_employee_id);
					if (!frm.doc.vendor_billing_status || frm.doc.vendor_billing_status === "Not Applicable") {
						frm.set_value("vendor_billing_status", "Pending Invoice");
					}
				} else {
					frm.set_value("is_outsourced_employee", 0);
					frm.set_value("vendor_billing_status", "Not Applicable");
				}
			}
		);
	}
});
