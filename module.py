"""
Staff Module Configuration

This file defines the module metadata and navigation for the Staff module.
Employee management including schedules and service assignments.
Used by the @module_view decorator to automatically render navigation tabs.
"""
from django.utils.translation import gettext_lazy as _

# Module Identification
MODULE_ID = "staff"
MODULE_NAME = _("Staff")
MODULE_ICON = "people-outline"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "hr"  # Changed from "services" to valid category

# Target Industries (business verticals this module is designed for)
MODULE_INDUSTRIES = [
    "beauty",     # Beauty & wellness
    "restaurant", # Restaurants
    "bar",        # Bars & pubs
    "hotel",      # Hotels & lodging
    "retail",     # Retail stores
    "healthcare", # Healthcare
]

# Sidebar Menu Configuration
MENU = {
    "label": _("Staff"),
    "icon": "people-outline",
    "order": 30,
    "show": True,
}

# Internal Navigation (Tabs)
NAVIGATION = [
    {
        "id": "dashboard",
        "label": _("Overview"),
        "icon": "grid-outline",
        "view": "",
    },
    {
        "id": "list",
        "label": _("Team"),
        "icon": "people-outline",
        "view": "list",
    },
    {
        "id": "schedules",
        "label": _("Schedules"),
        "icon": "calendar-outline",
        "view": "schedules",
    },
    {
        "id": "settings",
        "label": _("Settings"),
        "icon": "settings-outline",
        "view": "settings",
    },
]

# Module Dependencies
DEPENDENCIES = ["services>=1.0.0"]

# Default Settings
SETTINGS = {
    "require_service_assignment": True,
    "allow_schedule_overlap": False,
}

# Permissions
PERMISSIONS = [
    "staff.view_staffmember",
    "staff.add_staffmember",
    "staff.change_staffmember",
    "staff.delete_staffmember",
    "staff.view_schedule",
    "staff.manage_schedule",
]
