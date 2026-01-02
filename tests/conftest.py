"""
Pytest fixtures for staff module tests.
"""
import pytest
from datetime import date, time, timedelta
from decimal import Decimal

from staff.models import (
    StaffConfig,
    StaffRole,
    StaffMember,
    StaffSchedule,
    StaffWorkingHours,
    StaffTimeOff,
    StaffService,
)


@pytest.fixture(autouse=True)
def disable_debug_toolbar(settings):
    """Disable debug toolbar for tests."""
    settings.DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda request: False}
    settings.DEBUG = False
    if hasattr(settings, 'INSTALLED_APPS'):
        settings.INSTALLED_APPS = [
            app for app in settings.INSTALLED_APPS if 'debug_toolbar' not in app
        ]


@pytest.fixture
def config():
    """Get or create staff config."""
    return StaffConfig.get_config()


@pytest.fixture
def role():
    """Create a staff role."""
    return StaffRole.objects.create(
        name='Stylist',
        description='Hair stylist',
        order=1,
        is_active=True,
    )


@pytest.fixture
def secondary_role():
    """Create a secondary role."""
    return StaffRole.objects.create(
        name='Manager',
        description='Store manager',
        order=0,
        is_active=True,
    )


@pytest.fixture
def inactive_role():
    """Create an inactive role."""
    return StaffRole.objects.create(
        name='Trainee',
        description='In training',
        order=2,
        is_active=False,
    )


@pytest.fixture
def staff_member(role):
    """Create a staff member."""
    return StaffMember.objects.create(
        first_name='John',
        last_name='Doe',
        email='john@example.com',
        phone='+1234567890',
        employee_id='EMP001',
        role=role,
        status='active',
        is_bookable=True,
        hire_date=date.today() - timedelta(days=365),
        hourly_rate=Decimal('25.00'),
        commission_rate=Decimal('10.00'),
    )


@pytest.fixture
def inactive_staff(role):
    """Create an inactive staff member."""
    return StaffMember.objects.create(
        first_name='Jane',
        last_name='Smith',
        email='jane@example.com',
        role=role,
        status='inactive',
        is_bookable=False,
    )


@pytest.fixture
def on_leave_staff(role):
    """Create a staff member on leave."""
    return StaffMember.objects.create(
        first_name='Bob',
        last_name='Wilson',
        email='bob@example.com',
        role=role,
        status='on_leave',
        is_bookable=True,
    )


@pytest.fixture
def staff_schedule(staff_member):
    """Create a staff schedule."""
    return StaffSchedule.objects.create(
        staff=staff_member,
        name='Regular Schedule',
        is_default=True,
        is_active=True,
    )


@pytest.fixture
def working_hours(staff_schedule):
    """Create working hours for Monday."""
    return StaffWorkingHours.objects.create(
        schedule=staff_schedule,
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        end_time=time(17, 0),
        break_start=time(12, 0),
        break_end=time(13, 0),
        is_working=True,
    )


@pytest.fixture
def full_week_schedule(staff_schedule):
    """Create working hours for full week."""
    hours = []
    for day in range(7):
        is_weekend = day >= 5  # Weekend off
        wh = StaffWorkingHours.objects.create(
            schedule=staff_schedule,
            day_of_week=day,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_working=not is_weekend,
        )
        hours.append(wh)
    return hours


@pytest.fixture
def time_off_request(staff_member):
    """Create a pending time off request."""
    return StaffTimeOff.objects.create(
        staff=staff_member,
        leave_type='vacation',
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=14),
        reason='Annual vacation',
        status='pending',
    )


@pytest.fixture
def approved_time_off(staff_member):
    """Create an approved time off."""
    return StaffTimeOff.objects.create(
        staff=staff_member,
        leave_type='sick',
        start_date=date.today() - timedelta(days=3),
        end_date=date.today() - timedelta(days=1),
        status='approved',
    )


@pytest.fixture
def rejected_time_off(staff_member):
    """Create a rejected time off."""
    return StaffTimeOff.objects.create(
        staff=staff_member,
        leave_type='personal',
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=31),
        reason='Personal matters',
        status='rejected',
    )
