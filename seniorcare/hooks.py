app_name = "seniorcare"
app_title = "Seniorcare"
app_publisher = "Senior Circle"
app_description = "Residential Senior Care Facility Management App for Senior Circle"
app_email = "info@seniorcircle.com"
app_license = "mit"

# Installation & Migration Hooks
# ------------------------------
after_migrate = ["seniorcare.setup.setup_senior_care"]
after_install = "seniorcare.setup.setup_senior_care"

# DocType Class Overrides
# -----------------------
override_doctype_class = {
	"Payroll Entry": "seniorcare.payroll.CustomPayrollEntry"
}

# Document Events
# ---------------
doc_events = {
	"Employee": {
		"validate": "seniorcare.employee.validate_employee"
	},
	"Salary Slip": {
		"before_insert": "seniorcare.salary_slip.before_insert_salary_slip",
		"validate": "seniorcare.salary_slip.validate_salary_slip"
	},
	"Purchase Invoice": {
		"validate": "seniorcare.purchase_invoice.validate_purchase_invoice",
		"on_submit": "seniorcare.purchase_invoice.on_submit_purchase_invoice",
		"on_cancel": "seniorcare.purchase_invoice.on_cancel_purchase_invoice"
	}
}

# Doctype JS
# ----------
doctype_js = {
	"Payroll Entry": "public/js/payroll_entry.js",
	"Salary Slip": "public/js/salary_slip.js"
}
