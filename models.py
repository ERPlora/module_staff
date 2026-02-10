"""Staff module models."""

from datetime import date, datetime, time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import HubBaseModel


# =============================================================================
# Settings
# =============================================================================

class StaffSettings(HubBaseModel):
    """Per-hub staff settings."""

    # Working hours defaults
    default_work_start = models.TimeField(
        _("Default Work Start"), default=time(9, 0)
    )
    default_work_end = models.TimeField(
        _("Default Work End"), default=time(18, 0)
    )
    default_break_duration = models.PositiveIntegerField(
        _("Default Break Duration (minutes)"), default=60
    )

    # Scheduling
    min_advance_booking = models.PositiveIntegerField(
        _("Minimum Advance Booking (hours)"), default=1,
        help_text=_("Minimum hours before appointment can be booked")
    )
    max_daily_hours = models.PositiveIntegerField(
        _("Maximum Daily Hours"), default=12,
        validators=[MaxValueValidator(24)]
    )
    overtime_threshold = models.PositiveIntegerField(
        _("Overtime Threshold (hours/week)"), default=40
    )

    # Display
    show_staff_photos = models.BooleanField(_("Show Staff Photos"), default=True)
    show_staff_bio = models.BooleanField(_("Show Staff Bio"), default=True)
    allow_staff_selection = models.BooleanField(
        _("Allow Staff Selection"), default=True,
        help_text=_("Allow customers to select specific staff member")
    )

    # Notifications
    notify_new_appointment = models.BooleanField(_("Notify on New Appointment"), default=True)
    notify_cancellation = models.BooleanField(_("Notify on Cancellation"), default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'staff_settings'
        verbose_name = _("Staff Settings")
        verbose_name_plural = _("Staff Settings")
        unique_together = [('hub_id',)]

    def __str__(self):
        return f"Staff Settings (Hub {self.hub_id})"

    @classmethod
    def get_settings(cls, hub_id):
        settings, _ = cls.all_objects.get_or_create(hub_id=hub_id)
        return settings


# =============================================================================
# Roles
# =============================================================================

class StaffRole(HubBaseModel):
    """Staff roles for categorization."""

    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    color = models.CharField(
        _("Color"), max_length=7, blank=True,
        help_text=_("Hex color code")
    )
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'staff_role'
        verbose_name = _("Staff Role")
        verbose_name_plural = _("Staff Roles")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


# =============================================================================
# Staff Members
# =============================================================================

class StaffMember(HubBaseModel):
    """Staff member model."""

    STATUS_CHOICES = [
        ('active', _("Active")),
        ('inactive', _("Inactive")),
        ('on_leave', _("On Leave")),
        ('terminated', _("Terminated")),
    ]

    # Basic info
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    photo = models.ImageField(
        _("Photo"), upload_to='staff/photos/', blank=True, null=True
    )

    # Employment
    employee_id = models.CharField(
        _("Employee ID"), max_length=50, blank=True
    )
    role = models.ForeignKey(
        StaffRole, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='members',
        verbose_name=_("Role")
    )
    user = models.ForeignKey(
        'accounts.LocalUser', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='staff_profile',
        verbose_name=_("User Account")
    )
    hire_date = models.DateField(_("Hire Date"), null=True, blank=True)
    termination_date = models.DateField(_("Termination Date"), null=True, blank=True)
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default='active'
    )

    # Bio
    bio = models.TextField(_("Bio"), blank=True)
    specialties = models.TextField(
        _("Specialties"), blank=True,
        help_text=_("Comma-separated list of specialties")
    )

    # Booking
    is_bookable = models.BooleanField(
        _("Is Bookable"), default=True,
        help_text=_("Can be booked for appointments")
    )
    color = models.CharField(
        _("Calendar Color"), max_length=7, blank=True,
        help_text=_("Color for calendar display")
    )
    booking_buffer = models.PositiveIntegerField(
        _("Booking Buffer (minutes)"), default=0,
        help_text=_("Buffer time between appointments")
    )

    # Compensation
    hourly_rate = models.DecimalField(
        _("Hourly Rate"), max_digits=10, decimal_places=2,
        default=Decimal('0.00')
    )
    commission_rate = models.DecimalField(
        _("Commission Rate (%)"), max_digits=5, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    # Display
    order = models.PositiveIntegerField(_("Order"), default=0)
    notes = models.TextField(_("Internal Notes"), blank=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'staff_member'
        verbose_name = _("Staff Member")
        verbose_name_plural = _("Staff Members")
        ordering = ['order', 'first_name', 'last_name']
        indexes = [
            models.Index(fields=['hub_id', 'status']),
            models.Index(fields=['hub_id', 'is_bookable']),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_available(self):
        return self.status == 'active' and self.is_bookable

    @property
    def years_of_service(self):
        if not self.hire_date:
            return 0
        end_date = self.termination_date or date.today()
        return (end_date - self.hire_date).days // 365

    def get_specialties_list(self):
        if not self.specialties:
            return []
        return [s.strip() for s in self.specialties.split(',') if s.strip()]


# =============================================================================
# Schedules
# =============================================================================

class StaffSchedule(HubBaseModel):
    """Weekly schedule template for a staff member."""

    staff = models.ForeignKey(
        StaffMember, on_delete=models.CASCADE,
        related_name='schedules', verbose_name=_("Staff Member")
    )
    name = models.CharField(
        _("Schedule Name"), max_length=100, default="Default Schedule"
    )
    is_default = models.BooleanField(_("Is Default"), default=True)
    effective_from = models.DateField(_("Effective From"), null=True, blank=True)
    effective_until = models.DateField(_("Effective Until"), null=True, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'staff_schedule'
        verbose_name = _("Staff Schedule")
        verbose_name_plural = _("Staff Schedules")
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.staff.full_name} - {self.name}"

    def save(self, *args, **kwargs):
        if self.is_default:
            StaffSchedule.objects.filter(
                staff=self.staff, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def is_applicable_on(self, target_date):
        if not self.is_active:
            return False
        if self.effective_from and target_date < self.effective_from:
            return False
        if self.effective_until and target_date > self.effective_until:
            return False
        return True


class StaffWorkingHours(HubBaseModel):
    """Working hours for a specific day of week."""

    DAY_CHOICES = [
        (0, _("Monday")),
        (1, _("Tuesday")),
        (2, _("Wednesday")),
        (3, _("Thursday")),
        (4, _("Friday")),
        (5, _("Saturday")),
        (6, _("Sunday")),
    ]

    schedule = models.ForeignKey(
        StaffSchedule, on_delete=models.CASCADE,
        related_name='working_hours', verbose_name=_("Schedule")
    )
    day_of_week = models.PositiveSmallIntegerField(
        _("Day of Week"), choices=DAY_CHOICES
    )
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    break_start = models.TimeField(_("Break Start"), null=True, blank=True)
    break_end = models.TimeField(_("Break End"), null=True, blank=True)
    is_working = models.BooleanField(_("Is Working Day"), default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'staff_working_hours'
        verbose_name = _("Working Hours")
        verbose_name_plural = _("Working Hours")
        ordering = ['day_of_week', 'start_time']
        unique_together = [('schedule', 'day_of_week')]

    def __str__(self):
        day_name = dict(self.DAY_CHOICES).get(self.day_of_week)
        if not self.is_working:
            return f"{day_name}: Day Off"
        return f"{day_name}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

    def clean(self):
        if self.is_working:
            if self.end_time <= self.start_time:
                raise ValidationError(_("End time must be after start time."))
            if self.break_start and self.break_end:
                if self.break_end <= self.break_start:
                    raise ValidationError(_("Break end must be after break start."))
                if self.break_start < self.start_time or self.break_end > self.end_time:
                    raise ValidationError(_("Break must be within working hours."))

    @property
    def working_minutes(self):
        if not self.is_working:
            return 0
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        total = (end - start).seconds // 60
        if self.break_start and self.break_end:
            b_start = datetime.combine(date.today(), self.break_start)
            b_end = datetime.combine(date.today(), self.break_end)
            total -= (b_end - b_start).seconds // 60
        return total


# =============================================================================
# Time Off
# =============================================================================

class StaffTimeOff(HubBaseModel):
    """Time off / vacation / leave for staff."""

    TYPE_CHOICES = [
        ('vacation', _("Vacation")),
        ('sick', _("Sick Leave")),
        ('personal', _("Personal Leave")),
        ('training', _("Training")),
        ('other', _("Other")),
    ]

    STATUS_CHOICES = [
        ('pending', _("Pending")),
        ('approved', _("Approved")),
        ('rejected', _("Rejected")),
        ('cancelled', _("Cancelled")),
    ]

    staff = models.ForeignKey(
        StaffMember, on_delete=models.CASCADE,
        related_name='time_off', verbose_name=_("Staff Member")
    )
    leave_type = models.CharField(
        _("Type"), max_length=20, choices=TYPE_CHOICES, default='vacation'
    )
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    start_time = models.TimeField(
        _("Start Time"), null=True, blank=True,
        help_text=_("For partial day off")
    )
    end_time = models.TimeField(
        _("End Time"), null=True, blank=True,
        help_text=_("For partial day off")
    )
    is_full_day = models.BooleanField(_("Full Day"), default=True)
    reason = models.TextField(_("Reason"), blank=True)
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    approved_by = models.ForeignKey(
        'accounts.LocalUser', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_time_off',
        verbose_name=_("Approved By")
    )
    approved_at = models.DateTimeField(_("Approved At"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'staff_time_off'
        verbose_name = _("Time Off")
        verbose_name_plural = _("Time Off")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.staff.full_name}: {self.start_date} - {self.end_date}"

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError(_("End date must be after start date."))

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    def conflicts_with(self, start_date, end_date):
        if self.status not in ['pending', 'approved']:
            return False
        return not (end_date < self.start_date or start_date > self.end_date)


# =============================================================================
# Staff Services
# =============================================================================

class StaffService(HubBaseModel):
    """Services that a staff member can provide."""

    staff = models.ForeignKey(
        StaffMember, on_delete=models.CASCADE,
        related_name='staff_services', verbose_name=_("Staff Member")
    )
    service = models.ForeignKey(
        'services.Service', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='staff_assignments',
        verbose_name=_("Service")
    )
    service_name = models.CharField(
        _("Service Name"), max_length=200,
        help_text=_("Cached service name")
    )
    custom_duration = models.PositiveIntegerField(
        _("Custom Duration (minutes)"), null=True, blank=True,
        help_text=_("Override service default duration")
    )
    custom_price = models.DecimalField(
        _("Custom Price"), max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text=_("Override service default price")
    )
    is_primary = models.BooleanField(
        _("Primary Service"), default=False,
        help_text=_("Primary/specialty service for this staff")
    )
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'staff_service'
        verbose_name = _("Staff Service")
        verbose_name_plural = _("Staff Services")
        unique_together = [('staff', 'service')]
        ordering = ['-is_primary', 'service_name']

    def __str__(self):
        return f"{self.staff.full_name} - {self.service_name}"
