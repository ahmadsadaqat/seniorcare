// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.query_reports["Resident Medical Summary Report"] = {
	filters: [
		{
			fieldname: "resident_file",
			label: __("Resident File"),
			fieldtype: "Link",
			options: "Resident File"
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nActive\nTemporary Leave\nDischarged\nDeceased"
		},
		{
			fieldname: "primary_doctor",
			label: __("Primary Doctor"),
			fieldtype: "Link",
			options: "Doctor Provider"
		}
	]
};
