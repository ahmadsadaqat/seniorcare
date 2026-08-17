// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Outsourced Payroll Summary", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Fetch Salary Slips"), () => {
				frm.call({
					method: "fetch_salary_slips",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Fetching Salary Slips..."),
					callback: function () {
						frm.refresh();
					}
				});
			});

			if (!frm.doc.purchase_invoice && frm.doc.total_employees > 0) {
				frm.add_custom_button(__("Create Purchase Invoice"), () => {
					frm.call({
						method: "make_purchase_invoice",
						doc: frm.doc,
						freeze: true,
						freeze_message: __("Creating Purchase Invoice..."),
						callback: function (r) {
							if (r.message) {
								frappe.set_route("Form", "Purchase Invoice", r.message);
							}
						}
					});
				}, __("Actions"));
			}
		}
	},
	vendor_service_charge(frm) {
		frm.trigger("recalculate");
	},
	other_charges(frm) {
		frm.trigger("recalculate");
	},
	tax_amount(frm) {
		frm.trigger("recalculate");
	},
	recalculate(frm) {
		let total = flt(frm.doc.payroll_amount) + flt(frm.doc.vendor_service_charge) + flt(frm.doc.other_charges) + flt(frm.doc.tax_amount);
		frm.set_value("vendor_invoice_amount", total);
	}
});
