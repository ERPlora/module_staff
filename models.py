"""
Staff module models.
Manages staff members, schedules, working hours, and availability.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta, time, date
from decimal import Decimal


class StaffConfig(models.Model):
    """
    Singleton configuration for staff module.
    """
    # Working hours defaults
    default_work_start = models.TimeField(
        _("Default Work Start"),
        default=time(9, 0)
    )
    default_work_end = models.TimeField(
        _("Default Work End"),
        default=time(18, 0)
    )
    default_break_duration = models.PositiveIntegerField(
        _("Default Break Duration (minutes)"),
        default=60
    )

    # Scheduling options
    min_advance_booking = models.PositiveIntegerField(
        _("Minimum Advance Booking (hours)"),
        default=1,
        help_text=_("Minimum hours before appointment can be booked")
    )
    max_daily_hours = models.PositiveIntegerField(
        _("Maximum Daily Hours"),
        default=12,
        validators=[MaxValueValidator(24)]
    )
    overtime_threshold = models.PositiveIntegerField(
        _("Overtime Threshold (hours/week)"),
        default=40
    )

    # Display options
    show_staff_photos = models.BooleanField(
        _("Show Staff Photos"),
        default=True
    )
    show_staff_bio = models.BooleanField(
        _("Show Staff Bio"),
        default=True
    )
    allow_staff_selection = models.BooleanField(
        _("Allow Staff Selection"),
        default=True,
        help_text=_("Allow customers to select specific staff member")
    )

    # Notification settings
    notify_new_appointment = models.BooleanField(
        _("Notify on New Appointment"),
        default=True
    )
    notify_cancellation = models.BooleanField(
        _("Notify on Cancellation"),
        default=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Staff Configuration")
        verbose_name_plural = _("Staff Configuration")

    def __str__(self):
        return "Staff Configuration"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration."""
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class StaffRole(models.Model):
    """
    Staff roles for categorization and permissions.
    """
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    color = models.CharField(
        _("Color"),
        max_length=7,
        blank=True,
        help_text=_("Hex color code")
    )
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Staff Role")
        verbose_name_plural = _("Staff Roles")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class StaffMember(models.Model):
    """
    Staff member model.
    Represents an employee who can provide services and be booked.
    """
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
        _("Photo"),
        upload_to='staff/photos/',
        blank=True,
        null=True
    )

    # Employment details
    employee_id = models.CharField(
        _("Employee ID"),
        max_length=50,
        blank=True,
        unique=True,
        null=True
    )
    role = models.ForeignKey(
        StaffRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name=_("Role")
    )
    hire_date = models.DateField(_("Hire Date"), null=True, blank=True)
    termination_date = models.DateField(_("Termination Date"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Bio and presentation
    bio = models.TextField(_("Bio"), blank=True)
    specialties = models.TextField(
        _("Specialties"),
        blank=True,
        help_text=_("Comma-separated list of specialties")
    )

    # Booking settings
    is_bookable = models.BooleanField(
        _("Is Bookable"),
        default=True,
        help_text=_("Can be booked for appointments")
    )
    color = models.CharField(
        _("Calendar Color"),
        max_length=7,
        blank=True,
        help_text=_("Color for calendar display")
    )
    booking_buffer = models.PositiveIntegerField(
        _("Booking Buffer (minutes)"),
        default=0,
        help_text=_("Buffer time between appointments")
    )

    # Compensation (for commission calculations)
    hourly_rate = models.DecimalField(
        _("Hourly Rate"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    commission_rate = models.DecimalField(
        _("Commission Rate (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    # Link to LocalUser (optional)
    user_id = models.PositiveIntegerField(
        _("User ID"),
        null=True,
        blank=True,
        help_text=_("Link to LocalUser for login access")
    )

    # Display
    order = models.PositiveIntegerField(_("Order"), default=0)

    # Metadata
    notes = models.TextField(_("Internal Notes"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Staff Member")
        verbose_name_plural = _("Staff Members")
        ordering = ['order', 'first_name', 'last_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        """Get full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_available(self):
        """Check if staff member is available for booking."""
        return self.status == 'active' and self.is_bookable

    @property
    def years_of_service(self):
        """Calculate years of service."""
        if not self.hire_date:
            return 0
        end_date = self.termination_date or date.today()
        delta = end_date - self.hire_date
        return delta.days // 365

    def get_specialties_list(self):
        """Get specialties as list."""
        if not self.specialties:
            return []
        return [s.strip() for s in self.specialties.split(',') if s.strip()]


class StaffSchedule(models.Model):
    """
    Weekly schedule template for a staff member.
    """
    staff = models.ForeignKey(
        StaffMember,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_("Staff Member")
    )
    name = models.CharField(
        _("Schedule Name"),
        max_length=100,
        default="Default Schedule"
    )
    is_default = models.BooleanField(
        _("Is Default"),
        default=True
    )
    effective_from = models.DateField(
        _("Effective From"),
        null=True,
        blank=True
    )
    effective_until = models.DateField(
        _("Effective Until"),
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Staff Schedule")
        verbose_name_plural = _("Staff Schedules")
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.staff.full_name} - {self.name}"

    def save(self, *args, **kwargs):
        # Ensure only one default schedule per staff
        if self.is_default:
            StaffSchedule.objects.filter(
                staff=self.staff,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def is_applicable_on(self, target_date):
        """Check if schedule is applicable on given date."""
        if not self.is_active:
            return False
        if self.effective_from and target_date < self.effective_from:
            return False
        if self.effective_until and target_date > self.effective_until:
            return False
        return True


class StaffWorkingHours(models.Model):
    """
    Working hours for a specific day of week.
    """
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
        StaffSchedule,
        on_delete=models.CASCADE,
        related_name='working_hours',
        verbose_name=_("Schedule")
    )
    day_of_week = models.PositiveSmallIntegerField(
        _("Day of Week"),
        choices=DAY_CHOICES
    )
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    break_start = models.TimeField(
        _("Break Start"),
        null=True,
        blank=True
    )
    break_end = models.TimeField(
        _("Break End"),
        null=True,
        blank=True
    )
    is_working = models.BooleanField(
        _("Is Working Day"),
        default=True
    )

    class Meta:
        verbose_name = _("Working Hours")
        verbose_name_plural = _("Working Hours")
        ordering = ['day_of_week', 'start_time']
        unique_together = ['schedule', 'day_of_week']

    def __str__(self):
        day_name = dict(self.DAY_CHOICES).get(self.day_of_week)
        if not self.is_working:
            return f"{day_name}: Day Off"
        return f"{day_name}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

    def clean(self):
        """Validate working hours."""
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
        """Calculate total working minutes for the day."""
        if not self.is_working:
            return 0

        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        total = (end - start).seconds // 60

        if self.break_start and self.break_end:
            break_start = datetime.combine(date.today(), self.break_start)
            break_end = datetime.combine(date.today(), self.break_end)
            total -= (break_end - break_start).seconds // 60

        return total


class StaffTimeOff(models.Model):
    """
    Time off / vacation / leave for staff.
    """
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
        StaffMember,
        on_delete=models.CASCADE,
        related_name='time_off',
        verbose_name=_("Staff Member")
    )
    leave_type = models.CharField(
        _("Type"),
        max_length=20,
        choices=TYPE_CHOICES,
        default='vacation'
    )
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    start_time = models.TimeField(
        _("Start Time"),
        null=True,
        blank=True,
        help_text=_("For partial day off")
    )
    end_time = models.TimeField(
        _("End Time"),
        null=True,
        blank=True,
        help_text=_("For partial day off")
    )
    is_full_day = models.BooleanField(
        _("Full Day"),
        default=True
    )
    reason = models.TextField(_("Reason"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='approved'
    )
    approved_by_id = models.PositiveIntegerField(
        _("Approved By"),
        null=True,
        blank=True
    )
    approved_at = models.DateTimeField(
        _("Approved At"),
        null=True,
        blank=True
    )
    notes = models.TextField(_("Notes"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Time Off")
        verbose_name_plural = _("Time Off")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.staff.full_name}: {self.start_date} - {self.end_date}"

    def clean(self):
        """Validate time off dates."""
        if self.end_date < self.start_date:
            raise ValidationError(_("End date must be after start date."))

    @property
    def duration_days(self):
        """Calculate duration in days."""
        return (self.end_date - self.start_date).days + 1

    def conflicts_with(self, start_date, end_date):
        """Check if time off conflicts with date range."""
        if self.status not in ['pending', 'approved']:
            return False
        return not (end_date < self.start_date or start_date > self.end_date)


class StaffService(models.Model):
    """
    Services that a staff member can provide.
    Links staff to services module.
    """
    staff = models.ForeignKey(
        StaffMember,
        on_delete=models.CASCADE,
        related_name='staff_services',
        verbose_name=_("Staff Member")
    )
    service_id = models.PositiveIntegerField(
        _("Service ID"),
        help_text=_("ID from services module")
    )
    service_name = models.CharField(
        _("Service Name"),
        max_length=200,
        help_text=_("Cached service name")
    )
    custom_duration = models.PositiveIntegerField(
        _("Custom Duration (minutes)"),
        null=True,
        blank=True,
        help_text=_("Override service default duration")
    )
    custom_price = models.DecimalField(
        _("Custom Price"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Override service default price")
    )
    is_primary = models.BooleanField(
        _("Primary Service"),
        default=False,
        help_text=_("Primary/specialty service for this staff")
    )
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Staff Service")
        verbose_name_plural = _("Staff Services")
        unique_together = ['staff', 'service_id']
        ordering = ['-is_primary', 'service_name']

    def __str__(self):
        return f"{self.staff.full_name} - {self.service_name}"
