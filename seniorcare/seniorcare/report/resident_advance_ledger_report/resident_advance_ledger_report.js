// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.query_reports["Resident Advance Ledger Report"] = {
	filters: [
		{
			fieldname: "resident_file",
			label: __("Resident File"),
			fieldtype: "Link",
			options: "Resident File"
		},
		{
			fieldname: "advance_type",
			label: __("Advance Type"),
			fieldtype: "Select",
			options: "\nMedical Advance\nPersonal Advance"
		}
	]
};
