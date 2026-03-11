"""
AI context for the Staff module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Staff

### Models

**StaffRole**
- name (str), description, color (hex), order (int), is_active (bool)
- Used to categorize staff members (e.g. Therapist, Stylist, Receptionist)

**StaffMember**
- first_name, last_name, email, phone, photo
- employee_id (str), role (FK → StaffRole), user (FK → accounts.LocalUser, optional)
- hire_date, termination_date, status: active | inactive | on_leave | terminated
- bio, specialties (comma-separated string → use get_specialties_list())
- is_bookable (bool), color (hex for calendar), booking_buffer (minutes between appointments)
- hourly_rate (Decimal), commission_rate (Decimal, 0–100%)
- order (int for display sort)
- Property: full_name, is_available (status==active AND is_bookable), years_of_service

**StaffSchedule**
- staff (FK → StaffMember), name, is_default (bool), effective_from, effective_until, is_active
- Only one schedule per staff can have is_default=True (auto-enforced on save)
- Related: working_hours (StaffWorkingHours)

**StaffWorkingHours**
- schedule (FK → StaffSchedule), day_of_week (0=Mon … 6=Sun)
- start_time, end_time, break_start (optional), break_end (optional), is_working (bool)
- Unique: (schedule, day_of_week)
- Property: working_minutes (net of break)

**StaffTimeOff**
- staff (FK → StaffMember), leave_type: vacation | sick | personal | training | other
- start_date, end_date, is_full_day (bool), start_time/end_time (partial-day only)
- status: pending | approved | rejected | cancelled
- approved_by (FK → accounts.LocalUser), approved_at
- Property: duration_days

**StaffService**
- staff (FK → StaffMember), service (FK → services.Service), service_name (cached)
- custom_duration (override, minutes), custom_price (override)
- is_primary (bool), is_active (bool)
- Unique: (staff, service)

### Key flows

1. **Create staff member**: Create StaffRole if needed → Create StaffMember with role, status=active
2. **Set availability**: Create StaffSchedule (is_default=True) → Create StaffWorkingHours for each working day
3. **Assign services**: Create StaffService linking staff to services.Service records
4. **Request time off**: Create StaffTimeOff with status=pending → approve (set status=approved, approved_by, approved_at)
5. **Deactivate staff**: Set StaffMember.status = terminated + termination_date

### Relationships

- StaffMember.user → accounts.LocalUser (optional link to login account)
- StaffMember.role → StaffRole
- StaffService.service → services.Service
- StaffTimeOff.approved_by → accounts.LocalUser
- time_control.ClockRecord.employee → StaffMember
- time_control.DailySummary.employee → StaffMember
- appointments.Appointment.staff → accounts.LocalUser (not StaffMember directly)
"""
