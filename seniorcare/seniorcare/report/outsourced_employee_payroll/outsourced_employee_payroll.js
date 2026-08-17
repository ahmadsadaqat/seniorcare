// Copyright (c) 2026, Senior Circle and contributors
// For license information, please see license.txt

frappe.query_reports["Outsourced Employee Payroll"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company")
		},
		{
			fieldname: "from_date",
			label: __("Payroll Period From"),
			fieldtype: "Date"
		},
		{
			fieldname: "to_date",
			label: __("Payroll Period To"),
			fieldtype: "Date"
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier"
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee"
		},
		{
			fieldname: "payroll_entry",
			label: __("Payroll Entry"),
			fieldtype: "Link",
			options: "Payroll Entry"
		},
		{
			fieldname: "billing_status",
			label: __("Billing Status"),
			fieldtype: "Select",
			options: "\nNot Applicable\nPending Invoice\nInvoiced\nCancelled"
		}
	]
};
