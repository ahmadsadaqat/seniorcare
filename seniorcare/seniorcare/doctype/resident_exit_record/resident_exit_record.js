// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resident Exit Record", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Pending Settlement") {
			const approverRoles = ["Senior Care Approver", "Senior Care Manager", "System Manager"];
			const userRoles = frappe.user_roles || [];
			const hasApproverRole = approverRoles.some(r => userRoles.includes(r));

			if (hasApproverRole) {
				frm.add_custom_button(__("Approve & Finalize Settlement"), () => {
					frappe.prompt(
						[
							{
								fieldname: "remarks",
								fieldtype: "Small Text",
								label: __("Settlement Remarks"),
							}
						],
						(values) => {
							frappe.call({
								method: "seniorcare.seniorcare.doctype.resident_exit_record.resident_exit_record.approve_settlement",
								args: {
									record_name: frm.doc.name,
									remarks: values.remarks,
								},
								freeze: true,
								callback(r) {
									if (!r.exc) {
										frm.reload_doc();
									}
								}
							});
						},
						__("Finalize Exit Settlement"),
						__("Confirm Discharge")
					);
				}).addClass("btn-primary");
			}
		}

		frm.trigger("toggle_fields");
	},

	toggle_fields(frm) {
		frm.set_df_property("total_dues", "read_only", 1);
		frm.set_df_property("net_refund_amount", "read_only", 1);
	},

	resident_file(frm) {
		if (!frm.doc.resident_file) return;

		frappe.call({
			method: "seniorcare.seniorcare.doctype.resident_exit_record.resident_exit_record.fetch_resident_settlement_data",
			args: { resident_file: frm.doc.resident_file },
			callback(r) {
				if (r.message) {
					frm.set_value("security_deposit_held", r.message.security_deposit_held || 0);
					frm.set_value("medical_advance_balance", r.message.medical_advance_balance || 0);
					frm.set_value("personal_advance_balance", r.message.personal_advance_balance || 0);
					frm.set_value("outstanding_invoices", r.message.outstanding_invoices || 0);
					if (r.message.notice_period_days && !frm.doc.notice_period_days) {
						frm.set_value("notice_period_days", r.message.notice_period_days);
					}
					frm.trigger("calculate_totals");
				}
			}
		});
	},

	outstanding_invoices(frm) { frm.trigger("calculate_totals"); },
	pending_charges(frm) { frm.trigger("calculate_totals"); },
	damages(frm) { frm.trigger("calculate_totals"); },
	notice_period_penalty(frm) { frm.trigger("calculate_totals"); },
	security_deposit_held(frm) { frm.trigger("calculate_totals"); },
	medical_advance_balance(frm) { frm.trigger("calculate_totals"); },
	personal_advance_balance(frm) { frm.trigger("calculate_totals"); },
	total_deductions(frm) { frm.trigger("calculate_totals"); },

	calculate_totals(frm) {
		const dues = flt(frm.doc.outstanding_invoices)
			+ flt(frm.doc.pending_charges)
			+ flt(frm.doc.damages)
			+ flt(frm.doc.notice_period_penalty);
		frm.set_value("total_dues", dues);

		if (!frm.doc.total_deductions) {
			frm.set_value("total_deductions", dues);
		}

		const deposits = flt(frm.doc.security_deposit_held)
			+ flt(frm.doc.medical_advance_balance)
			+ flt(frm.doc.personal_advance_balance);

		frm.set_value("net_refund_amount", deposits - flt(frm.doc.total_deductions));
	}
});
