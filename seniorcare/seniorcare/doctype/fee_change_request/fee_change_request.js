// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fee Change Request", {
	refresh(frm) {
		// Auto-fetch current value when resident or component changes
		if (frm.doc.resident_file && frm.doc.fee_component && !frm.doc.current_value) {
			frm.trigger("fetch_current_value");
		}

		// Show Approve / Reject buttons for approvers on submitted docs
		if (frm.doc.docstatus === 1 && frm.doc.status === "Pending Approval") {
			if (frappe.user_roles.includes(frm.doc.approver_role || "Senior Care Approver")
				|| frappe.user_roles.includes("System Manager")) {

				frm.add_custom_button(__("Approve"), function () {
					frappe.prompt(
						{ label: "Remarks", fieldtype: "Small Text", fieldname: "remarks" },
						function (values) {
							frappe.call({
								method: "seniorcare.seniorcare.doctype.fee_change_request.fee_change_request.approve_fee_change",
								args: {
									fee_change_request: frm.doc.name,
									remarks: values.remarks || "",
								},
								callback: function () {
									frm.reload_doc();
								},
							});
						},
						__("Approve Fee Change"),
						__("Approve")
					);
				}, __("Action")).addClass("btn-primary");

				frm.add_custom_button(__("Reject"), function () {
					frappe.prompt(
						{ label: "Remarks", fieldtype: "Small Text", fieldname: "remarks", reqd: 1 },
						function (values) {
							frappe.call({
								method: "seniorcare.seniorcare.doctype.fee_change_request.fee_change_request.reject_fee_change",
								args: {
									fee_change_request: frm.doc.name,
									remarks: values.remarks,
								},
								callback: function () {
									frm.reload_doc();
								},
							});
						},
						__("Reject Fee Change"),
						__("Reject")
					);
				}, __("Action")).addClass("btn-danger");
			}
		}

		// Status indicator
		if (frm.doc.status === "Effective") {
			frm.page.set_indicator(__("Effective"), "green");
		} else if (frm.doc.status === "Approved") {
			frm.page.set_indicator(__("Approved (Future-dated)"), "blue");
		} else if (frm.doc.status === "Pending Approval") {
			frm.page.set_indicator(__("Pending Approval"), "orange");
		} else if (frm.doc.status === "Rejected") {
			frm.page.set_indicator(__("Rejected"), "red");
		}
	},

	resident_file(frm) {
		frm.trigger("fetch_current_value");
	},

	fee_component(frm) {
		frm.trigger("fetch_current_value");
	},

	fetch_current_value(frm) {
		if (!frm.doc.resident_file || !frm.doc.fee_component) return;

		const field_map = {
			"Occupancy Fee": "occupancy_fee",
			"Attendant Fee": "attendant_fee",
			"Other Fixed Charges": "other_fixed_charges",
		};

		const field = field_map[frm.doc.fee_component];
		if (!field) return;

		frappe.db.get_value("Resident File", frm.doc.resident_file, field, (r) => {
			if (r) {
				frm.set_value("current_value", r[field] || 0);
			}
		});
	},
});
