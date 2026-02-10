from django.utils.translation import gettext_lazy as _

MODULE_ID = 'staff'
MODULE_NAME = _('Staff')

MENU = {
    'label': _('Staff'),
    'icon': 'people-outline',
    'order': 50,
}

NAVIGATION = [
    {'id': 'dashboard', 'label': _('Overview'), 'icon': 'stats-chart-outline', 'view': ''},
    {'id': 'list', 'label': _('Staff'), 'icon': 'people-outline', 'view': 'list'},
    {'id': 'schedules', 'label': _('Schedules'), 'icon': 'calendar-outline', 'view': 'schedules'},
    {'id': 'roles', 'label': _('Roles'), 'icon': 'shield-outline', 'view': 'roles'},
    {'id': 'settings', 'label': _('Settings'), 'icon': 'settings-outline', 'view': 'settings'},
]

# Module Dependencies
DEPENDENCIES = ['services']
