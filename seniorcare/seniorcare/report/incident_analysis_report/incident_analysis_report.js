// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.query_reports["Incident Analysis Report"] = {
	filters: [
		{
			fieldname: "resident_file",
			label: __("Resident File"),
			fieldtype: "Link",
			options: "Resident File"
		},
		{
			fieldname: "incident_type",
			label: __("Incident Type"),
			fieldtype: "Select",
			options: "\nFall\nMedication Error\nBehavioral\nMedical Emergency\nInjury\nProperty Damage\nOther"
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nOpen\nUnder Review\nAction Required\nClosed"
		}
	]
};
