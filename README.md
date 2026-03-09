# Staff

## Overview

| Property | Value |
|----------|-------|
| **Module ID** | `staff` |
| **Version** | `1.0.0` |
| **Dependencies** | `services` |

## Dependencies

This module requires the following modules to be installed:

- `services`

## Models

### `StaffSettings`

Per-hub staff settings.

| Field | Type | Details |
|-------|------|---------|
| `default_work_start` | TimeField |  |
| `default_work_end` | TimeField |  |
| `default_break_duration` | PositiveIntegerField |  |
| `min_advance_booking` | PositiveIntegerField |  |
| `max_daily_hours` | PositiveIntegerField |  |
| `overtime_threshold` | PositiveIntegerField |  |
| `show_staff_photos` | BooleanField |  |
| `show_staff_bio` | BooleanField |  |
| `allow_staff_selection` | BooleanField |  |
| `notify_new_appointment` | BooleanField |  |
| `notify_cancellation` | BooleanField |  |

**Methods:**

- `get_settings()`

### `StaffRole`

Staff roles for categorization.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=100 |
| `description` | TextField | optional |
| `color` | CharField | max_length=7, optional |
| `order` | PositiveIntegerField |  |
| `is_active` | BooleanField |  |

### `StaffMember`

Staff member model.

| Field | Type | Details |
|-------|------|---------|
| `first_name` | CharField | max_length=100 |
| `last_name` | CharField | max_length=100 |
| `email` | EmailField | max_length=254, optional |
| `phone` | CharField | max_length=20, optional |
| `photo` | ImageField | max_length=100, optional |
| `employee_id` | CharField | max_length=50, optional |
| `role` | ForeignKey | → `staff.StaffRole`, on_delete=SET_NULL, optional |
| `user` | ForeignKey | → `accounts.LocalUser`, on_delete=SET_NULL, optional |
| `hire_date` | DateField | optional |
| `termination_date` | DateField | optional |
| `status` | CharField | max_length=20, choices: active, inactive, on_leave, terminated |
| `bio` | TextField | optional |
| `specialties` | TextField | optional |
| `is_bookable` | BooleanField |  |
| `color` | CharField | max_length=7, optional |
| `booking_buffer` | PositiveIntegerField |  |
| `hourly_rate` | DecimalField |  |
| `commission_rate` | DecimalField |  |
| `order` | PositiveIntegerField |  |
| `notes` | TextField | optional |

**Methods:**

- `get_specialties_list()`

**Properties:**

- `full_name`
- `is_available`
- `years_of_service`

### `StaffSchedule`

Weekly schedule template for a staff member.

| Field | Type | Details |
|-------|------|---------|
| `staff` | ForeignKey | → `staff.StaffMember`, on_delete=CASCADE |
| `name` | CharField | max_length=100 |
| `is_default` | BooleanField |  |
| `effective_from` | DateField | optional |
| `effective_until` | DateField | optional |
| `is_active` | BooleanField |  |

**Methods:**

- `is_applicable_on()`

### `StaffWorkingHours`

Working hours for a specific day of week.

| Field | Type | Details |
|-------|------|---------|
| `schedule` | ForeignKey | → `staff.StaffSchedule`, on_delete=CASCADE |
| `day_of_week` | PositiveSmallIntegerField | choices: 0, 1, 2, 3, 4, 5, ... |
| `start_time` | TimeField |  |
| `end_time` | TimeField |  |
| `break_start` | TimeField | optional |
| `break_end` | TimeField | optional |
| `is_working` | BooleanField |  |

**Properties:**

- `working_minutes`

### `StaffTimeOff`

Time off / vacation / leave for staff.

| Field | Type | Details |
|-------|------|---------|
| `staff` | ForeignKey | → `staff.StaffMember`, on_delete=CASCADE |
| `leave_type` | CharField | max_length=20, choices: vacation, sick, personal, training, other |
| `start_date` | DateField |  |
| `end_date` | DateField |  |
| `start_time` | TimeField | optional |
| `end_time` | TimeField | optional |
| `is_full_day` | BooleanField |  |
| `reason` | TextField | optional |
| `status` | CharField | max_length=20, choices: pending, approved, rejected, cancelled |
| `approved_by` | ForeignKey | → `accounts.LocalUser`, on_delete=SET_NULL, optional |
| `approved_at` | DateTimeField | optional |
| `notes` | TextField | optional |

**Methods:**

- `conflicts_with()`

**Properties:**

- `duration_days`

### `StaffService`

Services that a staff member can provide.

| Field | Type | Details |
|-------|------|---------|
| `staff` | ForeignKey | → `staff.StaffMember`, on_delete=CASCADE |
| `service` | ForeignKey | → `services.Service`, on_delete=SET_NULL, optional |
| `service_name` | CharField | max_length=200 |
| `custom_duration` | PositiveIntegerField | optional |
| `custom_price` | DecimalField | optional |
| `is_primary` | BooleanField |  |
| `is_active` | BooleanField |  |

## Cross-Module Relationships

| From | Field | To | on_delete | Nullable |
|------|-------|----|-----------|----------|
| `StaffMember` | `role` | `staff.StaffRole` | SET_NULL | Yes |
| `StaffMember` | `user` | `accounts.LocalUser` | SET_NULL | Yes |
| `StaffSchedule` | `staff` | `staff.StaffMember` | CASCADE | No |
| `StaffWorkingHours` | `schedule` | `staff.StaffSchedule` | CASCADE | No |
| `StaffTimeOff` | `staff` | `staff.StaffMember` | CASCADE | No |
| `StaffTimeOff` | `approved_by` | `accounts.LocalUser` | SET_NULL | Yes |
| `StaffService` | `staff` | `staff.StaffMember` | CASCADE | No |
| `StaffService` | `service` | `services.Service` | SET_NULL | Yes |

## URL Endpoints

Base path: `/m/staff/`

| Path | Name | Method |
|------|------|--------|
| `(root)` | `index` | GET |
| `dashboard/` | `dashboard` | GET |
| `list/` | `list` | GET |
| `create/` | `create` | GET/POST |
| `<uuid:pk>/` | `detail` | GET |
| `<uuid:pk>/edit/` | `edit` | GET |
| `<uuid:pk>/delete/` | `delete` | GET/POST |
| `<uuid:pk>/toggle/` | `toggle` | GET |
| `schedules/` | `schedules` | GET |
| `<uuid:staff_pk>/schedule/create/` | `schedule_create` | GET/POST |
| `schedule/<uuid:pk>/` | `schedule_detail` | GET |
| `schedule/<uuid:pk>/edit/` | `schedule_edit` | GET |
| `schedule/<uuid:pk>/delete/` | `schedule_delete` | GET/POST |
| `schedule/<uuid:schedule_pk>/hours/save/` | `working_hours_save` | GET/POST |
| `<uuid:staff_pk>/time-off/` | `time_off_list` | GET |
| `<uuid:staff_pk>/time-off/create/` | `time_off_create` | GET/POST |
| `time-off/<uuid:pk>/edit/` | `time_off_edit` | GET |
| `time-off/<uuid:pk>/delete/` | `time_off_delete` | GET/POST |
| `time-off/<uuid:pk>/approve/` | `time_off_approve` | GET |
| `time-off/<uuid:pk>/reject/` | `time_off_reject` | GET |
| `<uuid:staff_pk>/services/` | `staff_services` | GET |
| `<uuid:staff_pk>/services/save/` | `staff_services_save` | GET/POST |
| `roles/` | `role_list` | GET |
| `roles/add/` | `role_add` | GET/POST |
| `roles/<uuid:pk>/edit/` | `role_edit` | GET |
| `roles/<uuid:pk>/delete/` | `role_delete` | GET/POST |
| `settings/` | `settings` | GET |
| `settings/save/` | `settings_save` | GET/POST |
| `settings/toggle/` | `settings_toggle` | GET |
| `settings/input/` | `settings_input` | GET |
| `settings/reset/` | `settings_reset` | GET |
| `api/search/` | `api_search` | GET |
| `api/available/` | `api_available` | GET |
| `api/<uuid:pk>/schedule/` | `api_staff_schedule` | GET |

## Permissions

| Permission | Description |
|------------|-------------|
| `staff.manage_settings` | Manage Settings |

**Role assignments:**

- **admin**: All permissions
- **manager**: 
- **employee**: 

## Navigation

| View | Icon | ID | Fullpage |
|------|------|----|----------|
| Overview | `stats-chart-outline` | `dashboard` | No |
| Staff | `people-outline` | `list` | No |
| Schedules | `calendar-outline` | `schedules` | No |
| Roles | `shield-outline` | `roles` | No |
| Settings | `settings-outline` | `settings` | No |

## AI Tools

Tools available for the AI assistant:

### `list_staff_members`

List staff members with filters. Returns name, role, status, specialties, bookable status.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: active, inactive, on_leave, terminated |
| `role_id` | string | No | Filter by staff role ID |
| `is_bookable` | boolean | No | Filter by bookable status |

### `create_staff_member`

Create a new staff member.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `first_name` | string | Yes |  |
| `last_name` | string | Yes |  |
| `email` | string | No |  |
| `phone` | string | No |  |
| `role_id` | string | No | Staff role ID |
| `specialties` | string | No | Specialties/skills |
| `is_bookable` | boolean | No | Can be booked for appointments |
| `hourly_rate` | string | No | Hourly rate |
| `commission_rate` | string | No | Commission percentage |
| `bio` | string | No |  |
| `color` | string | No | Calendar color |

### `list_staff_roles`

List staff roles (e.g., 'Estilista Senior', 'Ayudante').

### `create_staff_role`

Create a staff role (e.g., 'Estilista', 'Cocinero', 'Recepcionista').

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes |  |
| `description` | string | No |  |
| `color` | string | No | Hex color |

### `list_staff_time_off`

List staff time off requests.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `staff_id` | string | No |  |
| `status` | string | No | pending, approved, rejected, cancelled |
| `limit` | integer | No |  |

### `create_time_off_request`

Create a time off request for a staff member.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `staff_id` | string | Yes |  |
| `leave_type` | string | Yes | vacation, sick, personal, training, other |
| `start_date` | string | Yes |  |
| `end_date` | string | Yes |  |
| `reason` | string | No |  |
| `is_full_day` | boolean | No |  |

### `assign_service_to_staff`

Assign a service to a staff member (for appointments/bookings).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `staff_id` | string | Yes |  |
| `service_id` | string | Yes |  |
| `custom_duration` | integer | No | Custom duration in minutes |
| `custom_price` | string | No | Custom price |
| `is_primary` | boolean | No | Is this their primary service |

### `get_staff_settings`

Get staff module settings.

## File Structure

```
CHANGELOG.md
README.md
TODO.md
__init__.py
ai_tools.py
apps.py
forms.py
locale/
  es/
    LC_MESSAGES/
      django.po
migrations/
  0001_initial.py
  __init__.py
models.py
module.py
static/
  icons/
    ion/
templates/
  staff/
    pages/
      create.html
      detail.html
      edit.html
      index.html
      list.html
      roles.html
      schedule_detail.html
      schedules.html
      settings.html
      staff_services.html
      time_off.html
    partials/
      _role_form.html
      _schedule_form.html
      _time_off_form.html
      dashboard.html
      detail.html
      form.html
      list.html
      roles.html
      schedule_detail.html
      schedules.html
      settings.html
      staff_list_items.html
      staff_services.html
      time_off_list.html
tests/
  __init__.py
  conftest.py
  test_models.py
  test_services.py
  test_views.py
urls.py
views.py
```
