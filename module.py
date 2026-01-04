"""
Staff Module Configuration

Staff and employee management.
"""
from django.utils.translation import gettext_lazy as _

MODULE_ID = "staff"
MODULE_NAME = _("Staff")
MODULE_ICON = "people-outline"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "core"

MODULE_INDUSTRIES = ["retail", "restaurant", "bar", "cafe", "beauty", "healthcare"]

MENU = {
    "label": _("Staff"),
    "icon": "people-outline",
    "order": 70,
    "show": True,
}

NAVIGATION = [
    {"id": "dashboard", "label": _("Overview"), "icon": "grid-outline", "view": ""},
    {"id": "staff", "label": _("Staff"), "icon": "people-outline", "view": "staff"},
    {"id": "schedules", "label": _("Schedules"), "icon": "calendar-outline", "view": "schedules"},
    {"id": "settings", "label": _("Settings"), "icon": "settings-outline", "view": "settings"},
]

DEPENDENCIES = []

SETTINGS = {
    "track_time": True,
    "require_clock_in": False,
    "overtime_threshold": 40,
}

PERMISSIONS = [
    ("view_staff", _("Can view staff")),
    ("add_staff", _("Can add staff")),
    ("change_staff", _("Can change staff")),
    ("delete_staff", _("Can delete staff")),
    ("view_schedule", _("Can view schedules")),
    ("manage_schedule", _("Can manage schedules")),
    ("view_timesheet", _("Can view timesheets")),
    ("manage_timesheet", _("Can manage timesheets")),
    ("view_settings", _("Can view settings")),
    ("change_settings", _("Can change settings")),
]

ROLE_PERMISSIONS = {
    "admin": ["*"],
    "manager": [
        "view_staff", "add_staff", "change_staff",
        "view_schedule", "manage_schedule",
        "view_timesheet", "manage_timesheet",
        "view_settings",
    ],
    "employee": ["view_staff", "view_schedule", "view_timesheet"],
}
