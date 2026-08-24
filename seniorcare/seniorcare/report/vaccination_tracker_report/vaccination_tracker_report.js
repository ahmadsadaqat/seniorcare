// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.query_reports["Vaccination Tracker Report"] = {
	filters: [
		{
			fieldname: "resident_file",
			label: __("Resident File"),
			fieldtype: "Link",
			options: "Resident File"
		},
		{
			fieldname: "vaccine_name",
			label: __("Vaccine Name"),
			fieldtype: "Select",
			options: "\nCOVID-19\nInfluenza (Flu)\nPneumococcal\nHepatitis B\nTetanus\nShingles\nOther"
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nCompleted\nPending\nOngoing"
		},
		{
			fieldname: "from_due_date",
			label: __("From Due Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "to_due_date",
			label: __("To Due Date"),
			fieldtype: "Date"
		}
	]
};
