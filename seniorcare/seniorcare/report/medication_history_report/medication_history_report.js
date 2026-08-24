// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.query_reports["Medication History Report"] = {
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
			options: "\nActive\nOn Hold"
		},
		{
			fieldname: "prescribed_by",
			label: __("Prescribed By"),
			fieldtype: "Link",
			options: "Doctor Provider"
		}
	]
};
