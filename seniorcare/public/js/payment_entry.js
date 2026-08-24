// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payment Entry", {
	refresh(frm) {
		frm.trigger("setup_senior_care_filters");
		frm.trigger("show_resident_balance_indicator");
	},

	setup_senior_care_filters(frm) {
		if (frm.doc.company) {
			const acc_filter = { company: frm.doc.company, is_group: 0 };
			frm.set_query("custom_security_deposit_liability_account", () => ({ filters: acc_filter }));
			frm.set_query("custom_medical_advance_liability_account", () => ({ filters: acc_filter }));
			frm.set_query("custom_personal_advance_liability_account", () => ({ filters: acc_filter }));
			frm.set_query("custom_medical_expense_account", () => ({ filters: acc_filter }));
			frm.set_query("custom_personal_expense_account", () => ({ filters: acc_filter }));
		}
	},

	custom_payment_purpose(frm) {
		if (frm.doc.custom_payment_purpose && frm.doc.custom_payment_purpose !== "Normal Payment") {
			// Auto-fill configured accounts from Senior Care Settings
			frappe.db.get_single_value("Senior Care Settings", "company").then(() => {
				frappe.call({
					method: "frappe.client.get",
					args: { doctype: "Senior Care Settings" },
					callback(r) {
						if (r.message) {
							const s = r.message;
							const purpose = frm.doc.custom_payment_purpose;

							if (["Security Deposit", "Security Deposit Refund"].includes(purpose)) {
								if (!frm.doc.custom_security_deposit_liability_account && s.security_deposit_liability_account) {
									frm.set_value("custom_security_deposit_liability_account", s.security_deposit_liability_account);
								}
							} else if (["Medical Advance", "Medical Advance Refund"].includes(purpose)) {
								if (!frm.doc.custom_medical_advance_liability_account && s.medical_advance_liability_account) {
									frm.set_value("custom_medical_advance_liability_account", s.medical_advance_liability_account);
								}
							} else if (["Personal Advance", "Personal Advance Refund"].includes(purpose)) {
								if (!frm.doc.custom_personal_advance_liability_account && s.personal_advance_liability_account) {
									frm.set_value("custom_personal_advance_liability_account", s.personal_advance_liability_account);
								}
							} else if (purpose === "Resident Medical Expense") {
								if (!frm.doc.custom_medical_expense_account && s.medical_expense_account) {
									frm.set_value("custom_medical_expense_account", s.medical_expense_account);
								}
								if (frm.doc.custom_funding_source === "Resident Medical Advance" && !frm.doc.custom_medical_advance_liability_account) {
									frm.set_value("custom_medical_advance_liability_account", s.medical_advance_liability_account);
								}
							} else if (purpose === "Resident Personal Expense") {
								if (!frm.doc.custom_personal_expense_account && s.personal_expense_account) {
									frm.set_value("custom_personal_expense_account", s.personal_expense_account);
								}
								if (frm.doc.custom_funding_source === "Resident Personal Advance" && !frm.doc.custom_personal_advance_liability_account) {
									frm.set_value("custom_personal_advance_liability_account", s.personal_advance_liability_account);
								}
							}
						}
					}
				});
			});

			if (frm.doc.party_type === "Customer" && frm.doc.party && !frm.doc.custom_resident) {
				frm.set_value("custom_resident", frm.doc.party);
			}
		}
		frm.trigger("show_resident_balance_indicator");
	},

	custom_resident(frm) {
		if (frm.doc.custom_resident && (!frm.doc.party || frm.doc.party !== frm.doc.custom_resident)) {
			if (frm.doc.party_type === "Customer") {
				frm.set_value("party", frm.doc.custom_resident);
			}
		}
		frm.trigger("show_resident_balance_indicator");
	},

	custom_funding_source(frm) {
		frm.trigger("custom_payment_purpose");
	},

	show_resident_balance_indicator(frm) {
		if (frm.doc.custom_resident && frm.doc.custom_payment_purpose && frm.doc.custom_payment_purpose !== "Normal Payment") {
			frappe.db.get_value("Resident File", { customer: frm.doc.custom_resident }, [
				"name", "security_deposit_balance", "medical_advance_balance", "personal_advance_balance"
			]).then(r => {
				if (r && r.message) {
					const res = r.message;
					let info = `<strong>Resident File:</strong> <a href="/app/resident-file/${res.name}" target="_blank">${res.name}</a> | `;
					info += `<strong>Deposit Bal:</strong> ${format_currency(res.security_deposit_balance)} | `;
					info += `<strong>Med Advance Bal:</strong> ${format_currency(res.medical_advance_balance)} | `;
					info += `<strong>Pers Advance Bal:</strong> ${format_currency(res.personal_advance_balance)}`;
					frm.dashboard.set_headline(info);
				}
			});
		} else {
			frm.dashboard.clear_headline();
		}
	}
});
