# Staff Module

Employee management for service-based businesses including schedules, service assignments, and availability.

## Features

- Staff member management
- Work schedule configuration
- Service assignments
- Availability tracking
- Staff calendar view
- Integration with Services and Appointments modules

## Installation

This module is installed automatically when activated in ERPlora Hub.

### Dependencies

- ERPlora Hub >= 1.0.0
- Required: `services` >= 1.0.0

## Configuration

Access module settings at `/m/staff/settings/`.

### Available Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `require_service_assignment` | boolean | `true` | Require service assignments |
| `allow_schedule_overlap` | boolean | `false` | Allow overlapping schedules |

## Usage

### Views

| View | URL | Description |
|------|-----|-------------|
| Overview | `/m/staff/` | Dashboard |
| Team | `/m/staff/list/` | Staff list |
| Schedules | `/m/staff/schedules/` | Schedule management |
| Settings | `/m/staff/settings/` | Module configuration |

## Permissions

| Permission | Description |
|------------|-------------|
| `staff.view_staffmember` | View staff members |
| `staff.add_staffmember` | Add staff members |
| `staff.change_staffmember` | Edit staff members |
| `staff.delete_staffmember` | Remove staff members |
| `staff.view_schedule` | View schedules |
| `staff.manage_schedule` | Manage schedules |

## Module Icon

Location: `static/icons/icon.svg`

Icon source: [React Icons - Ionicons 5](https://react-icons.github.io/react-icons/icons/io5/)

---

**Version:** 1.0.0
**Category:** services
**Author:** ERPlora Team
