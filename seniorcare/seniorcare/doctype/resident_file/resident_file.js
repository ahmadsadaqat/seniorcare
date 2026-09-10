// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resident File", {
	setup(frm) {
		frm.trigger("prevent_auto_save_on_attach");
	},

	onload(frm) {
		frm.trigger("prevent_auto_save_on_attach");
	},

	refresh(frm) {
		frm.trigger("prevent_auto_save_on_attach");
		frm.trigger("setup_custom_buttons");
		frm.trigger("filter_room_field");
	},

	prevent_auto_save_on_attach(frm) {
		const attach_fields = ["resident_photo", "dnr_document", "medical_documents"];
		attach_fields.forEach(fieldname => {
			const field = frm.get_field(fieldname);
			if (field && !field._auto_save_overridden) {
				field._auto_save_overridden = true;
				const orig_on_upload_complete = field.on_upload_complete.bind(field);
				field.on_upload_complete = async function(attachment) {
					if (this.frm && this.frm.is_new()) {
						await this.parse_validate_and_set_in_model(attachment.file_url);
						this.set_value(attachment.file_url);
						if (this.frm.attachments) {
							this.frm.attachments.update_attachment(attachment);
						}
						this.refresh();
					} else {
						orig_on_upload_complete(attachment);
					}
				};
			}
		});
	},

	setup_custom_buttons(frm) {
		if (!frm.is_new()) {
			// Standout Emergency Card Button
			frm.add_custom_button(__("Emergency Card"), () => {
				frm.trigger("show_emergency_card");
			}).addClass("btn-danger font-weight-bold");

			// Clinical & Medical Actions
			frm.add_custom_button(__("Book Appointment"), () => {
				frappe.new_doc("Doctor Appointment", {
					resident_file: frm.doc.name,
					doctor: frm.doc.primary_doctor
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Record Vitals"), () => {
				frappe.new_doc("Vital Signs Log", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Log Vaccination"), () => {
				frappe.new_doc("Vaccination Log", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Daily Health Log"), () => {
				frappe.new_doc("Daily Health Log", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Fall Risk Assessment"), () => {
				frappe.new_doc("Fall Risk Assessment", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Record Incident"), () => {
				frappe.new_doc("Incident Report", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("ADL Assessment"), () => {
				frappe.new_doc("ADL Assessment", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Resident Assessment"), () => {
				frappe.new_doc("Resident Assessment", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Wound Assessment"), () => {
				frappe.new_doc("Wound Assessment", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Create Lab Record"), () => {
				frappe.new_doc("Lab Record", {
					resident_file: frm.doc.name,
					ordered_by: frm.doc.primary_doctor
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Hospital Transfer"), () => {
				frappe.new_doc("Hospital Transfer", {
					resident_file: frm.doc.name,
					hospital: frm.doc.preferred_hospital
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Care Plan"), () => {
				frappe.new_doc("Care Plan", {
					resident_file: frm.doc.name
				});
			}, __("Clinical Actions"));

			frm.add_custom_button(__("Assign Attendant"), () => {
				const new_doc = frappe.model.get_new_doc("Attendant Assignment");
				frappe.set_route("Form", "Attendant Assignment", new_doc.name).then(() => {
					cur_frm.add_child("assigned_residents", {
						resident_file: frm.doc.name,
						resident_name: frm.doc.full_name,
						room_unit: frm.doc.room_unit,
						care_acuity_level: frm.doc.care_acuity_level
					});
					cur_frm.refresh_field("assigned_residents");
				});
			}, __("Actions"));

			// Financial & Commercial Actions
			frm.add_custom_button(__("New Contract"), () => {
				frappe.new_doc("Resident Contract", {
					resident_file: frm.doc.name,
					customer: frm.doc.customer
				});
			}, __("Financial Actions"));

			frm.add_custom_button(__("Refresh Financial Balances"), () => {
				frappe.call({
					method: "seniorcare.seniorcare.doctype.resident_file.resident_file.refresh_resident_financials",
					args: { resident_file: frm.doc.name },
					callback(r) {
						if (r.message) {
							frm.reload_doc();
							frappe.show_alert({ message: __("Financial balances updated from Payment Entries."), indicator: "green" });
						}
					}
				});
			}, __("Financial Actions"));

			frm.add_custom_button(__("Generate Monthly Invoice"), () => {
				frappe.call({
					method: "seniorcare.billing.generate_resident_invoice",
					args: { resident_file: frm.doc.name },
					callback(r) {
						if (r.message) {
							frappe.show_alert({ message: __("Draft Sales Invoice {0} created.", [r.message]), indicator: "green" });
							frappe.set_route("Form", "Sales Invoice", r.message);
						}
					}
				});
			}, __("Financial Actions"));

			frm.add_custom_button(__("Request Fee Change"), () => {
				frappe.new_doc("Fee Change Request", {
					resident_file: frm.doc.name
				});
			}, __("Financial Actions"));

			frm.add_custom_button(__("Initiate Exit Settlement"), () => {
				frappe.new_doc("Resident Exit Record", {
					resident_file: frm.doc.name
				});
			}, __("Financial Actions"));
		}
	},

	show_emergency_card(frm) {
		frappe.call({
			method: "seniorcare.seniorcare.doctype.resident_file.resident_file.get_emergency_card_data",
			args: { resident_file: frm.doc.name },
			freeze: true,
			freeze_message: __("Loading Emergency Card..."),
			callback(r) {
				if (!r.message) return;
				const data = r.message;

				const is_dnr = (data.dnr_directive || "").toUpperCase() === "DNR";
				const dnr_badge = is_dnr
					? `<span style="background: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px;">DNR (DO NOT RESUSCITATE)</span>`
					: `<span style="background: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px;">FULL CODE</span>`;

				const fall_badge_color = data.fall_risk_level === "High" ? "#dc3545" : (data.fall_risk_level === "Medium" ? "#fd7e14" : "#28a745");
				const blood_group_html = data.blood_group ? `<span style="background: #8b0000; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">${data.blood_group}</span>` : '<span class="text-muted">Unknown</span>';

				// Allergies HTML
				let allergies_html = "";
				if (data.allergies && data.allergies.length > 0) {
					allergies_html = data.allergies.map(a => {
						const bg = a.is_severe ? '#ffebee' : '#f5f5f5';
						const border = a.is_severe ? '#e53935' : '#bdbdbd';
						const color = a.is_severe ? '#b71c1c' : '#333';
						const icon = a.is_severe ? '⚠️ ' : '';
						return `<div style="background: ${bg}; border: 1px solid ${border}; color: ${color}; padding: 6px 10px; border-radius: 4px; margin-bottom: 6px; font-size: 12px;">
							<strong>${icon}${a.allergen}</strong> (${a.severity}) ${a.reaction ? '— ' + a.reaction : ''}
						</div>`;
					}).join("");
				} else {
					allergies_html = `<div style="color: #2e7d32; font-size: 12px; padding: 4px 0;">✓ No known allergies recorded (NKDA)</div>`;
				}

				// Diagnoses HTML
				let diagnoses_html = "";
				if (data.conditions && data.conditions.length > 0) {
					diagnoses_html = `<ul style="margin: 0; padding-left: 18px; font-size: 12px;">` +
						data.conditions.map(c => `<li><strong>${c.condition}</strong> <span class="text-muted">(${c.status} - ${c.severity})</span></li>`).join("") +
						`</ul>`;
				} else {
					diagnoses_html = `<div class="text-muted" style="font-size: 12px;">No active chronic diagnoses recorded</div>`;
				}

				// Medications HTML
				let meds_html = "";
				if (data.medications && data.medications.length > 0) {
					meds_html = `<table class="table table-bordered table-sm mb-0" style="font-size: 11px;">
						<thead>
							<tr style="background: #f8f9fa;">
								<th>Medicine</th>
								<th>Dose</th>
								<th>Freq</th>
								<th>Type</th>
							</tr>
						</thead>
						<tbody>` +
						data.medications.map(m => `<tr>
							<td><strong>${m.medicine}</strong></td>
							<td>${m.dose} ${m.unit}</td>
							<td>${m.frequency}</td>
							<td>${m.is_prn ? '<span class="badge badge-warning">PRN</span>' : 'Scheduled'}</td>
						</tr>`).join("") +
						`</tbody></table>`;
				} else {
					meds_html = `<div class="text-muted" style="font-size: 12px;">No active medications recorded</div>`;
				}

				// Emergency Contacts HTML
				let contacts_html = "";
				if (data.emergency_contacts && data.emergency_contacts.length > 0) {
					contacts_html = data.emergency_contacts.map(c => `
						<div style="margin-bottom: 6px; font-size: 12px; border-bottom: 1px dashed #eee; padding-bottom: 4px;">
							<strong>${c.name}</strong> <span class="badge badge-secondary">${c.relationship}</span><br>
							<span>📞 <strong>${c.phone || '-'}</strong></span> ${c.whatsapp ? ' | WA: ' + c.whatsapp : ''}
						</div>
					`).join("");
				} else {
					contacts_html = `<div class="text-muted" style="font-size: 12px;">No emergency contacts listed</div>`;
				}

				// Doctor & Hospital HTML
				let doctor_html = `<div style="font-size: 12px;">
					<strong>Doctor:</strong> ${data.doctor ? data.doctor.doctor_name : 'Not Assigned'}<br>
					<strong>Phone:</strong> ${data.doctor && data.doctor.phone ? '📞 ' + data.doctor.phone : '-'}<br>
					<strong>Hospital:</strong> ${data.preferred_hospital || (data.doctor ? data.doctor.organization_hospital : 'Standard ER')}
				</div>`;

				// Special Care Instructions
				let instructions = [];
				if (data.mobility_status) instructions.push(`<strong>Mobility:</strong> ${data.mobility_status}`);
				if (data.cognitive_status) instructions.push(`<strong>Cognition:</strong> ${data.cognitive_status}`);
				if (data.assistive_devices) instructions.push(`<strong>Assistive Devices:</strong> ${data.assistive_devices}`);
				if (data.dietary_restrictions) instructions.push(`<strong>Dietary:</strong> ${data.dietary_restrictions}`);
				if (data.special_care_instructions) instructions.push(`<strong>Special Care:</strong> ${data.special_care_instructions}`);
				if (data.isolation_precautions) instructions.push(`<strong>Precautions:</strong> ${data.isolation_precautions}`);
				if (data.medical_notes) instructions.push(`<strong>Medical Notes:</strong> ${data.medical_notes}`);
				const instructions_html = instructions.length > 0
					? `<div style="font-size: 11px; line-height: 1.5;">${instructions.join(' | ')}</div>`
					: `<div class="text-muted" style="font-size: 11px;">No special instructions noted</div>`;

				// Photo HTML
				const photo_html = data.resident_photo
					? `<img src="${data.resident_photo}" style="width: 100px; height: 110px; object-fit: cover; border-radius: 6px; border: 2px solid #ddd;">`
					: `<div style="width: 100px; height: 110px; background: #e0e0e0; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 28px; color: #888; border: 2px solid #ccc;">👤</div>`;

				const card_html = `
				<div id="senior-care-emergency-card-container" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #212529;">
					<!-- Emergency Card Box -->
					<div style="border: 3px solid #dc3545; border-radius: 8px; overflow: hidden; background: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
						<!-- Header Banner -->
						<div style="background: #dc3545; color: white; padding: 10px 16px; display: flex; justify-content: space-between; align-items: center;">
							<div>
								<span style="font-size: 16px; font-weight: 800; letter-spacing: 0.5px;">EMERGENCY MEDICAL PROFILE</span>
								<div style="font-size: 11px; opacity: 0.9;">SENIOR CIRCLE RESIDENT CARE</div>
							</div>
							<div>
								${dnr_badge}
							</div>
						</div>

						<!-- Identity Section -->
						<div style="padding: 14px 16px; background: #fff8f8; border-bottom: 2px solid #f5c6cb; display: flex; gap: 16px; align-items: center;">
							<div>${photo_html}</div>
							<div style="flex: 1;">
								<div style="font-size: 20px; font-weight: 800; color: #111;">${data.full_name}</div>
								<div style="font-size: 12px; color: #555; margin-bottom: 6px;">ID: <strong>${data.resident_id}</strong> ${data.cnic_national_id ? '| CNIC: ' + data.cnic_national_id : ''}</div>
								<div style="display: flex; gap: 10px; flex-wrap: wrap; font-size: 13px;">
									<span>Age: <strong>${data.age || '-'} yrs</strong> (${data.gender || '-'})</span>
									<span>Room: <strong style="background: #e3f2fd; color: #0d47a1; padding: 2px 6px; border-radius: 3px;">${data.room_unit}</strong></span>
									<span>Blood Group: ${blood_group_html}</span>
								</div>
								<div style="margin-top: 6px; display: flex; gap: 8px; font-size: 11px;">
									<span style="background: #eee; padding: 2px 6px; border-radius: 3px;">Acuity: <strong>${data.care_acuity_level}</strong></span>
									<span style="background: ${fall_badge_color}; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;">Fall Risk: ${data.fall_risk_level}</span>
								</div>
							</div>
						</div>

						<!-- Grid Details -->
						<div style="padding: 14px 16px;">
							<div class="row">
								<!-- Left Column: Allergies & Meds -->
								<div class="col-md-6" style="border-right: 1px solid #eee;">
									<div style="font-weight: bold; font-size: 13px; color: #dc3545; border-bottom: 1px solid #dc3545; padding-bottom: 3px; margin-bottom: 8px;">
										🚨 ALLERGIES & ADVERSE REACTIONS
									</div>
									${allergies_html}

									<div style="font-weight: bold; font-size: 13px; color: #0d47a1; border-bottom: 1px solid #0d47a1; padding-bottom: 3px; margin-top: 12px; margin-bottom: 8px;">
										💊 CURRENT MEDICATIONS (ACTIVE/PRN)
									</div>
									${meds_html}
								</div>

								<!-- Right Column: Diagnoses & Emergency Contacts -->
								<div class="col-md-6">
									<div style="font-weight: bold; font-size: 13px; color: #333; border-bottom: 1px solid #333; padding-bottom: 3px; margin-bottom: 8px;">
										🩺 ACTIVE MEDICAL DIAGNOSES
									</div>
									${diagnoses_html}

									<div style="font-weight: bold; font-size: 13px; color: #2e7d32; border-bottom: 1px solid #2e7d32; padding-bottom: 3px; margin-top: 12px; margin-bottom: 8px;">
										📞 EMERGENCY CONTACTS & PHYSICIAN
									</div>
									<div class="row">
										<div class="col-6">
											<div style="font-size: 11px; font-weight: bold; color: #666; margin-bottom: 4px;">PRIMARY CONTACT</div>
											${contacts_html}
										</div>
										<div class="col-6">
											<div style="font-size: 11px; font-weight: bold; color: #666; margin-bottom: 4px;">PRIMARY DOCTOR</div>
											${doctor_html}
										</div>
									</div>
								</div>
							</div>

							<!-- Bottom Care Instructions -->
							<div style="margin-top: 14px; padding-top: 10px; border-top: 2px solid #f0f0f0; background: #fafafa; padding: 10px; border-radius: 4px;">
								<div style="font-weight: bold; font-size: 12px; color: #555; margin-bottom: 4px;">⚠️ SPECIAL CARE INSTRUCTIONS & PRECAUTIONS</div>
								${instructions_html}
							</div>
						</div>
					</div>
				</div>
				`;

				let dialog = new frappe.ui.Dialog({
					title: __("Resident Emergency Medical Card"),
					size: "large",
					fields: [
						{
							fieldtype: "HTML",
							fieldname: "card_html_area"
						}
					],
					primary_action_label: __("Print Emergency Card"),
					primary_action: () => {
						frm.events.print_emergency_card(frm, card_html);
					}
				});

				dialog.get_field("card_html_area").$wrapper.html(card_html);
				dialog.show();
			}
		});
	},

	print_emergency_card(frm, html_content) {
		// Clean up existing print iframe
		$("#senior-care-print-frame").remove();

		// Create hidden iframe
		const iframe = document.createElement("iframe");
		iframe.id = "senior-care-print-frame";
		iframe.style.position = "fixed";
		iframe.style.right = "0";
		iframe.style.bottom = "0";
		iframe.style.width = "0";
		iframe.style.height = "0";
		iframe.style.border = "0";
		document.body.appendChild(iframe);

		const print_doc = iframe.contentWindow || iframe.contentDocument;
		const doc = print_doc.document || print_doc;

		doc.open();
		doc.write(`
			<!DOCTYPE html>
			<html>
			<head>
				<title>Emergency Medical Card - ${frm.doc.full_name || 'Resident'}</title>
				<style>
					@page {
						size: A4 portrait;
						margin: 10mm;
					}
					* {
						box-sizing: border-box;
						-webkit-print-color-adjust: exact !important;
						print-color-adjust: exact !important;
						color-adjust: exact !important;
					}
					body {
						font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
						background: #ffffff !important;
						margin: 0;
						padding: 0;
						color: #111;
					}
					.row {
						display: flex;
						flex-wrap: wrap;
						margin-right: -8px;
						margin-left: -8px;
					}
					.col-md-6, .col-6 {
						position: relative;
						width: 50%;
						padding-right: 8px;
						padding-left: 8px;
					}
					table {
						width: 100%;
						border-collapse: collapse;
					}
					th, td {
						border: 1px solid #dee2e6;
						padding: 4px 6px;
						text-align: left;
					}
					.badge {
						display: inline-block;
						padding: 2px 6px;
						font-size: 10px;
						font-weight: 700;
						border-radius: 3px;
					}
					.badge-warning { background-color: #ffc107; color: #212529; }
					.badge-secondary { background-color: #6c757d; color: #fff; }
					.badge-success { background-color: #28a745; color: #fff; }
				</style>
			</head>
			<body>
				<div style="max-width: 800px; margin: 0 auto; padding: 5px;">
					${html_content}
				</div>
			</body>
			</html>
		`);
		doc.close();

		setTimeout(() => {
			try {
				iframe.contentWindow.focus();
				iframe.contentWindow.print();
			} catch (e) {
				console.error("Iframe print error:", e);
				// Fallback to window.open
				const fallback = window.open("", "_blank");
				if (fallback) {
					fallback.document.write(doc.documentElement.outerHTML);
					fallback.document.close();
					fallback.focus();
					fallback.print();
				}
			}
		}, 350);
	},

	filter_room_field(frm) {
		frm.set_query("room_unit", () => {
			return {
				filters: [
					["Room", "occupancy_status", "in", ["Available", "Reserved"]],
				]
			};
		});
	},

	first_name(frm) {
		frm.trigger("set_full_name");
	},
	last_name(frm) {
		frm.trigger("set_full_name");
	},
	set_full_name(frm) {
		if (frm.doc.first_name) {
			let name = frm.doc.first_name + (frm.doc.last_name ? " " + frm.doc.last_name : "");
			frm.set_value("full_name", name.trim());
		}
	},

	date_of_birth(frm) {
		if (frm.doc.date_of_birth) {
			let dob = new Date(frm.doc.date_of_birth);
			let today = new Date();
			let age = today.getFullYear() - dob.getFullYear();
			let m = today.getMonth() - dob.getMonth();
			if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
				age--;
			}
			frm.set_value("age", Math.max(0, age));
		}
	}
});

frappe.ui.form.on("Senior Care Family Member", {
	is_poa(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.is_poa && row.family_member_name) {
			const str = `${row.family_member_name} (${row.relationship || "Family"}) - Ph: ${row.phone || ""}`.trim();
			frm.set_value("power_of_attorney", str);
		}
	},
	can_receive_updates(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.can_receive_updates && row.family_member_name) {
			const str = `${row.family_member_name} (${row.relationship || "Family"}) - Ph: ${row.phone || ""}`.trim();
			frm.set_value("primary_family_contact", str);
		}
	},
	can_approve_expenses(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.can_approve_expenses && row.family_member_name) {
			const str = `${row.family_member_name} (${row.relationship || "Family"}) - Ph: ${row.phone || ""}`.trim();
			frm.set_value("payer_billing_contact", str);
		}
	}
});

