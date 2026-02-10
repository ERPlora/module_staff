"""Staff forms."""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    StaffSettings,
    StaffRole,
    StaffMember,
    StaffSchedule,
    StaffWorkingHours,
    StaffTimeOff,
    StaffService,
)


class StaffMemberForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'employee_id', 'role', 'hire_date', 'status',
            'bio', 'specialties',
            'is_bookable', 'color', 'booking_buffer',
            'hourly_rate', 'commission_rate',
            'order', 'notes',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input'}),
            'last_name': forms.TextInput(attrs={'class': 'input'}),
            'email': forms.EmailInput(attrs={'class': 'input'}),
            'phone': forms.TextInput(attrs={'class': 'input'}),
            'employee_id': forms.TextInput(attrs={'class': 'input'}),
            'role': forms.Select(attrs={'class': 'select'}),
            'hire_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'select'}),
            'bio': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'specialties': forms.TextInput(attrs={'class': 'input'}),
            'is_bookable': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'color': forms.TextInput(attrs={'class': 'input', 'type': 'color'}),
            'booking_buffer': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0', 'max': '100'}),
            'order': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'textarea', 'rows': 2}),
        }


class StaffRoleForm(forms.ModelForm):
    class Meta:
        model = StaffRole
        fields = ['name', 'description', 'color', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'textarea', 'rows': 2}),
            'color': forms.TextInput(attrs={'class': 'input', 'type': 'color'}),
            'order': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }


class StaffScheduleForm(forms.ModelForm):
    class Meta:
        model = StaffSchedule
        fields = ['name', 'is_default', 'effective_from', 'effective_until', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'effective_from': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'effective_until': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }


class StaffWorkingHoursForm(forms.ModelForm):
    class Meta:
        model = StaffWorkingHours
        fields = ['day_of_week', 'start_time', 'end_time', 'break_start', 'break_end', 'is_working']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'select'}),
            'start_time': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'break_start': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'break_end': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'is_working': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }


class StaffTimeOffForm(forms.ModelForm):
    class Meta:
        model = StaffTimeOff
        fields = [
            'leave_type', 'start_date', 'end_date',
            'start_time', 'end_time', 'is_full_day', 'reason',
        ]
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'select'}),
            'start_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'is_full_day': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'reason': forms.Textarea(attrs={'class': 'textarea', 'rows': 2}),
        }


class StaffFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'input', 'placeholder': _('Search staff...')
    }))
    role = forms.UUIDField(required=False, widget=forms.HiddenInput())
    status = forms.ChoiceField(
        required=False,
        choices=[('', _('All statuses'))] + StaffMember.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'select'})
    )


class StaffSettingsForm(forms.ModelForm):
    class Meta:
        model = StaffSettings
        fields = [
            'default_work_start', 'default_work_end', 'default_break_duration',
            'min_advance_booking', 'max_daily_hours', 'overtime_threshold',
            'show_staff_photos', 'show_staff_bio', 'allow_staff_selection',
            'notify_new_appointment', 'notify_cancellation',
        ]
        widgets = {
            'default_work_start': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'default_work_end': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'default_break_duration': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'min_advance_booking': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
            'max_daily_hours': forms.NumberInput(attrs={'class': 'input', 'min': '1', 'max': '24'}),
            'overtime_threshold': forms.NumberInput(attrs={'class': 'input', 'min': '1'}),
            'show_staff_photos': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'show_staff_bio': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'allow_staff_selection': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'notify_new_appointment': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'notify_cancellation': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }
