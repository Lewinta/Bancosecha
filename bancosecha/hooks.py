app_name = "bancosecha"
app_title = "Bancosecha"
app_publisher = "Lewin Villar"
app_description = "A Custom App for Bancosecha"
app_email = "lewinvillar@tzcode.tech"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/bancosecha/css/bancosecha.css"
app_include_js = [
    "floating_button.bundle.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/bancosecha/css/bancosecha.css"
# web_include_js = "/assets/bancosecha/js/bancosecha.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "bancosecha/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Sales Invoice" : "public/js/sales_invoice.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Fixtures
# ----------

fixtures = [
    {
        "dt": "Custom DocPerm",
        "filters": { }
    },
    {
        "dt": "Custom Field",
        "filters": {
            "module": "Bancosecha"
        }
    },
    {
        "dt": "Property Setter",
        "filters": {
            "module": "Bancosecha"
        }
    },
    {
        "dt": "Print Format",
        "filters": {
            "module": "Bancosecha"
        }
    },
    {
        "dt": "Role Profile",
        "filters": {
            "name": [
                "in", [
                    "CEO"
                ]
            ]
        }
    },
    {
        "dt": "Module Profile",
        "filters": {
            "name": "Bancosecha"
        }
    },
    {
        "dt": "Workflow",
        "filters": {}
    },
    {
        "dt": "Workflow State",
        "filters": {}
    },
    {
        "dt": "Workflow Action",
        "filters": {}
    },
    
    

]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "bancosecha.utils.jinja_methods",
# 	"filters": "bancosecha.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "bancosecha.install.before_install"
# after_install = "bancosecha.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "bancosecha.uninstall.before_uninstall"
# after_uninstall = "bancosecha.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "bancosecha.utils.before_app_install"
# after_app_install = "bancosecha.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "bancosecha.utils.before_app_uninstall"
# after_app_uninstall = "bancosecha.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "bancosecha.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Invoice": {
		"validate": "bancosecha.bancosecha.controllers.sales_invoice.validate",
		"before_submit": "bancosecha.bancosecha.controllers.sales_invoice.before_submit",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"bancosecha.tasks.all"
# 	],
# 	"daily": [
# 		"bancosecha.tasks.daily"
# 	],
# 	"hourly": [
# 		"bancosecha.tasks.hourly"
# 	],
# 	"weekly": [
# 		"bancosecha.tasks.weekly"
# 	],
# 	"monthly": [
# 		"bancosecha.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "bancosecha.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "bancosecha.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "bancosecha.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["bancosecha.utils.before_request"]
# after_request = ["bancosecha.utils.after_request"]

# Job Events
# ----------
# before_job = ["bancosecha.utils.before_job"]
# after_job = ["bancosecha.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"bancosecha.auth.validate"
# ]

extend_bootinfo = "bancosecha.boot.boot_session"