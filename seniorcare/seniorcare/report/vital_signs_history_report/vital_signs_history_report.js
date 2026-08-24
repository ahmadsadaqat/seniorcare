// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.query_reports["Vital Signs History Report"] = {
	filters: [
		{
			fieldname: "resident_file",
			label: __("Resident File"),
			fieldtype: "Link",
			options: "Resident File"
		},
		{
			fieldname: "abnormal_reading",
			label: __("Abnormal Only?"),
			fieldtype: "Select",
			options: "\nNo\nYes"
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date"
		}
	]
};
