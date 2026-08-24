// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.query_reports["Daily Health Logs Report"] = {
	filters: [
		{
			fieldname: "resident_file",
			label: __("Resident File"),
			fieldtype: "Link",
			options: "Resident File"
		},
		{
			fieldname: "shift",
			label: __("Shift"),
			fieldtype: "Select",
			options: "\nMorning\nEvening\nNight"
		},
		{
			fieldname: "general_condition",
			label: __("General Condition"),
			fieldtype: "Select",
			options: "\nGood\nFair\nPoor"
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
