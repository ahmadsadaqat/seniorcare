// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.query_reports["Fall Risk Assessment History Report"] = {
	filters: [
		{
			fieldname: "resident_file",
			label: __("Resident File"),
			fieldtype: "Link",
			options: "Resident File"
		},
		{
			fieldname: "risk_level",
			label: __("Risk Level"),
			fieldtype: "Select",
			options: "\nLow\nModerate\nHigh"
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
