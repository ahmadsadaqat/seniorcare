// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attendant Assignment", {
	refresh(frm) {
		frm.trigger("setup_custom_buttons");
	},

	setup_custom_buttons(frm) {
		frm.add_custom_button(__("Fetch Residents"), () => {
			frm.trigger("show_fetch_residents_dialog");
		});
	},

	show_fetch_residents_dialog(frm) {
		let dialog = new frappe.ui.Dialog({
			title: __("Fetch Residents for Assignment"),
			size: "large",
			fields: [
				{
					fieldtype: "Select",
					fieldname: "resident_status",
					label: __("Resident Status"),
					options: "Active\nTrial\nAll",
					default: "Active"
				},
				{
					fieldtype: "Column Break"
				},
				{
					fieldtype: "Select",
					fieldname: "care_acuity_level",
					label: __("Care Acuity Level"),
					options: "\nIndependent\nAssisted\nSkilled Nursing\nMemory Care\nOther"
				},
				{
					fieldtype: "Section Break"
				},
				{
					fieldtype: "Button",
					fieldname: "btn_filter",
					label: __("Search / Refresh"),
					click: () => {
						load_residents();
					}
				},
				{
					fieldtype: "Section Break",
					label: __("Select Residents")
				},
				{
					fieldtype: "HTML",
					fieldname: "residents_table_area"
				}
			],
			primary_action_label: __("Add Selected Residents"),
			primary_action: () => {
				const selected = [];
				dialog.$wrapper.find(".resident-select-checkbox:checked").each(function () {
					selected.push($(this).data("resident"));
				});

				if (selected.length === 0) {
					frappe.msgprint(__("Please select at least one resident."));
					return;
				}

				const existing_res = (frm.doc.assigned_residents || []).map(r => r.resident_file);
				let added_count = 0;

				selected.forEach(res_data => {
					if (!existing_res.includes(res_data.name)) {
						frm.add_child("assigned_residents", {
							resident_file: res_data.name,
							resident_name: res_data.full_name,
							room_unit: res_data.room_unit,
							care_acuity_level: res_data.care_acuity_level
						});
						added_count++;
					}
				});

				frm.refresh_field("assigned_residents");
				dialog.hide();
				frappe.show_alert({
					message: __("{0} resident(s) added to assignment.", [added_count]),
					indicator: "green"
				});
			}
		});

		function load_residents() {
			const values = dialog.get_values() || {};
			frappe.call({
				method: "seniorcare.seniorcare.doctype.attendant_assignment.attendant_assignment.get_residents_for_assignment",
				args: {
					resident_status: values.resident_status || "Active",
					care_acuity_level: values.care_acuity_level || null
				},
				callback: (r) => {
					const residents = r.message || [];
					const existing_res = (frm.doc.assigned_residents || []).map(row => row.resident_file);

					if (residents.length === 0) {
						dialog.get_field("residents_table_area").$wrapper.html(
							`<div class="text-muted text-center py-4">${__("No residents found matching the criteria.")}</div>`
						);
						return;
					}

					let rows_html = residents.map(res => {
						const is_already_added = existing_res.includes(res.name);
						const res_json = JSON.stringify(res).replace(/"/g, "&quot;");
						return `
							<tr class="${is_already_added ? 'text-muted' : ''}">
								<td style="width: 40px; text-align: center;">
									<input type="checkbox" class="resident-select-checkbox" data-resident="${res_json}" ${is_already_added ? 'disabled' : 'checked'}>
								</td>
								<td><strong>${res.full_name || res.name}</strong> (${res.name})</td>
								<td>${res.room_unit || '<span class="text-muted">Unassigned</span>'}</td>
								<td>${res.care_acuity_level || '-'}</td>
								<td>${res.assigned_attendant_name || '<span class="text-muted">None</span>'}</td>
								<td>${is_already_added ? '<span class="badge badge-info">' + __("Already Added") + '</span>' : '<span class="badge badge-success">' + res.resident_status + '</span>'}</td>
							</tr>
						`;
					}).join("");

					let table_html = `
						<div style="max-height: 380px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: 4px;">
							<table class="table table-bordered table-hover mb-0" style="font-size: 13px;">
								<thead style="position: sticky; top: 0; background: var(--bg-color); z-index: 1;">
									<tr>
										<th style="width: 40px; text-align: center;">
											<input type="checkbox" id="select-all-residents" checked>
										</th>
										<th>${__("Resident Name")}</th>
										<th>${__("Room / Unit")}</th>
										<th>${__("Acuity Level")}</th>
										<th>${__("Current Attendant")}</th>
										<th>${__("Status")}</th>
									</tr>
								</thead>
								<tbody>
									${rows_html}
								</tbody>
							</table>
						</div>
					`;

					dialog.get_field("residents_table_area").$wrapper.html(table_html);

					dialog.$wrapper.find("#select-all-residents").on("change", function () {
						const checked = $(this).is(":checked");
						dialog.$wrapper.find(".resident-select-checkbox:not(:disabled)").prop("checked", checked);
					});
				}
			});
		}

		dialog.show();
		load_residents();
	}
});

frappe.ui.form.on("Attendant Assignment Item", {
	resident_file(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.resident_file) {
			frappe.db.get_value("Resident File", row.resident_file, ["full_name", "room_unit", "care_acuity_level"]).then(r => {
				if (r && r.message) {
					frappe.model.set_value(cdt, cdn, "resident_name", r.message.full_name);
					frappe.model.set_value(cdt, cdn, "room_unit", r.message.room_unit);
					frappe.model.set_value(cdt, cdn, "care_acuity_level", r.message.care_acuity_level);
				}
			});
		}
	}
});
