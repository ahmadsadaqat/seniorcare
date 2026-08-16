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

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/seniorcare/css/seniorcare.css"
# app_include_js = "/assets/seniorcare/js/seniorcare.js"

# DocType Class Overrides
# -----------------------
# override_doctype_class = {}

# Document Events
# ---------------
# doc_events = {}

# Scheduled Tasks
# ---------------
# scheduler_events = {}
