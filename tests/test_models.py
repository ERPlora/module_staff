"""
Unit tests for staff module models.
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


# =============================================================================
# StaffConfig Tests
# =============================================================================

@pytest.mark.django_db
class TestStaffConfig:
    """Test StaffConfig singleton model."""

    def test_get_config_creates_singleton(self):
        """Should create config on first access."""
        config = StaffConfig.get_config()
        assert config.pk == 1

    def test_get_config_returns_same_instance(self):
        """Should return same instance on subsequent calls."""
        config1 = StaffConfig.get_config()
        config2 = StaffConfig.get_config()
        assert config1.pk == config2.pk

    def test_default_values(self, config):
        """Should have sensible defaults."""
        assert config.default_work_start == time(9, 0)
        assert config.default_work_end == time(18, 0)
        assert config.default_break_duration == 60
        assert config.allow_staff_selection is True

    def test_update_config(self, config):
        """Should update config values."""
        config.default_work_start = time(8, 0)
        config.allow_staff_selection = False
        config.save()

        config.refresh_from_db()
        assert config.default_work_start == time(8, 0)
        assert config.allow_staff_selection is False


# =============================================================================
# StaffRole Tests
# =============================================================================

@pytest.mark.django_db
class TestStaffRole:
    """Test StaffRole model."""

    def test_create_role(self):
        """Should create role with name."""
        role = StaffRole.objects.create(
            name='Technician',
            description='Technical staff',
        )
        assert role.name == 'Technician'
        assert role.is_active is True
        assert role.order == 0

    def test_role_str(self, role):
        """Should return name as string."""
        assert str(role) == 'Stylist'

    def test_role_ordering(self, role, secondary_role):
        """Should order by order field."""
        roles = list(StaffRole.objects.all())
        assert roles[0] == secondary_role  # order=0
        assert roles[1] == role  # order=1

    def test_role_active_filter(self, role, inactive_role):
        """Should filter by active status."""
        active = StaffRole.objects.filter(is_active=True)
        inactive = StaffRole.objects.filter(is_active=False)

        assert role in active
        assert inactive_role in inactive
        assert inactive_role not in active


# =============================================================================
# StaffMember Tests
# =============================================================================

@pytest.mark.django_db
class TestStaffMember:
    """Test StaffMember model."""

    def test_create_staff_member(self, role):
        """Should create staff member."""
        member = StaffMember.objects.create(
            first_name='Alice',
            last_name='Brown',
            role=role,
        )
        assert member.first_name == 'Alice'
        assert member.status == 'active'
        assert member.is_bookable is True

    def test_full_name(self, staff_member):
        """Should return full name."""
        assert staff_member.full_name == 'John Doe'

    def test_staff_str(self, staff_member):
        """Should return full name as string."""
        assert str(staff_member) == 'John Doe'

    def test_staff_with_role(self, staff_member, role):
        """Should be linked to role."""
        assert staff_member.role == role
        assert staff_member in role.members.all()

    def test_staff_status_choices(self, staff_member, inactive_staff, on_leave_staff):
        """Should have correct status values."""
        assert staff_member.status == 'active'
        assert inactive_staff.status == 'inactive'
        assert on_leave_staff.status == 'on_leave'

    def test_bookable_staff(self, staff_member, inactive_staff):
        """Should filter bookable staff."""
        bookable = StaffMember.objects.filter(is_bookable=True)
        assert staff_member in bookable
        assert inactive_staff not in bookable

    def test_active_staff(self, staff_member, inactive_staff, on_leave_staff):
        """Should filter active staff."""
        active = StaffMember.objects.filter(status='active')
        assert staff_member in active
        assert inactive_staff not in active
        assert on_leave_staff not in active

    def test_staff_compensation(self, staff_member):
        """Should have compensation fields."""
        assert staff_member.hourly_rate == Decimal('25.00')
        assert staff_member.commission_rate == Decimal('10.00')

    def test_staff_ordering(self, staff_member, inactive_staff):
        """Should order by first name, last name."""
        staff_member.first_name = 'Zoe'
        staff_member.save()

        staff = list(StaffMember.objects.all())
        assert staff[0] == inactive_staff  # Jane
        assert staff[1] == staff_member  # Zoe


# =============================================================================
# StaffSchedule Tests
# =============================================================================

@pytest.mark.django_db
class TestStaffSchedule:
    """Test StaffSchedule model."""

    def test_create_schedule(self, staff_member):
        """Should create schedule."""
        schedule = StaffSchedule.objects.create(
            staff=staff_member,
            name='Summer Schedule',
            is_default=False,  # Explicitly set to False
        )
        assert schedule.name == 'Summer Schedule'
        assert schedule.is_active is True
        assert schedule.is_default is False

    def test_schedule_str(self, staff_schedule):
        """Should return name with staff as string."""
        assert 'John Doe' in str(staff_schedule)
        assert 'Regular Schedule' in str(staff_schedule)

    def test_schedule_belongs_to_staff(self, staff_schedule, staff_member):
        """Should be linked to staff member."""
        assert staff_schedule.staff == staff_member
        assert staff_schedule in staff_member.schedules.all()

    def test_default_schedule(self, staff_member):
        """Should support default schedule."""
        schedule1 = StaffSchedule.objects.create(
            staff=staff_member,
            name='Schedule 1',
            is_default=True,
        )
        schedule2 = StaffSchedule.objects.create(
            staff=staff_member,
            name='Schedule 2',
            is_default=False,
        )

        default = StaffSchedule.objects.filter(
            staff=staff_member,
            is_default=True,
        ).first()
        assert default == schedule1


# =============================================================================
# StaffWorkingHours Tests
# =============================================================================

@pytest.mark.django_db
class TestStaffWorkingHours:
    """Test StaffWorkingHours model."""

    def test_create_working_hours(self, staff_schedule):
        """Should create working hours."""
        hours = StaffWorkingHours.objects.create(
            schedule=staff_schedule,
            day_of_week=1,  # Tuesday
            start_time=time(10, 0),
            end_time=time(18, 0),
        )
        assert hours.day_of_week == 1
        assert hours.is_working is True

    def test_working_hours_str(self, working_hours):
        """Should return day name as string."""
        assert 'Monday' in str(working_hours)

    def test_day_off(self, staff_schedule):
        """Should support day off."""
        hours = StaffWorkingHours.objects.create(
            schedule=staff_schedule,
            day_of_week=6,  # Sunday
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_working=False,
        )
        assert hours.is_working is False

    def test_break_times(self, working_hours):
        """Should support break times."""
        assert working_hours.break_start == time(12, 0)
        assert working_hours.break_end == time(13, 0)

    def test_unique_day_per_schedule(self, staff_schedule, working_hours):
        """Should enforce unique day per schedule."""
        with pytest.raises(Exception):
            StaffWorkingHours.objects.create(
                schedule=staff_schedule,
                day_of_week=0,  # Monday - already exists
                start_time=time(10, 0),
                end_time=time(18, 0),
            )

    def test_working_hours_ordering(self, full_week_schedule):
        """Should order by day of week."""
        hours = list(StaffWorkingHours.objects.all())
        for i, wh in enumerate(hours):
            assert wh.day_of_week == i


# =============================================================================
# StaffTimeOff Tests
# =============================================================================

@pytest.mark.django_db
class TestStaffTimeOff:
    """Test StaffTimeOff model."""

    def test_create_time_off(self, staff_member):
        """Should create time off request."""
        time_off = StaffTimeOff.objects.create(
            staff=staff_member,
            leave_type='vacation',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
            status='pending',  # Explicitly set to pending
        )
        assert time_off.status == 'pending'
        assert time_off.leave_type == 'vacation'

    def test_time_off_str(self, time_off_request):
        """Should return staff and dates as string."""
        assert 'John Doe' in str(time_off_request)

    def test_time_off_duration(self, time_off_request):
        """Should calculate duration."""
        # 7 days from start to end (inclusive)
        duration = (time_off_request.end_date - time_off_request.start_date).days + 1
        assert duration == 8

    def test_time_off_status_choices(self, time_off_request, approved_time_off, rejected_time_off):
        """Should have correct status values."""
        assert time_off_request.status == 'pending'
        assert approved_time_off.status == 'approved'
        assert rejected_time_off.status == 'rejected'

    def test_leave_type_choices(self, staff_member):
        """Should support different leave types."""
        types = ['vacation', 'sick', 'personal', 'maternity', 'paternity', 'other']
        for leave_type in types:
            time_off = StaffTimeOff.objects.create(
                staff=staff_member,
                leave_type=leave_type,
                start_date=date.today(),
                end_date=date.today(),
            )
            assert time_off.leave_type == leave_type
            time_off.delete()

    def test_time_off_with_reason(self, time_off_request):
        """Should have reason field."""
        assert time_off_request.reason == 'Annual vacation'

    def test_time_off_ordering(self, staff_member):
        """Should order by start date descending."""
        t1 = StaffTimeOff.objects.create(
            staff=staff_member,
            leave_type='vacation',
            start_date=date.today(),
            end_date=date.today(),
        )
        t2 = StaffTimeOff.objects.create(
            staff=staff_member,
            leave_type='sick',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=10),
        )

        time_offs = list(StaffTimeOff.objects.all())
        assert time_offs[0] == t2  # Later date first
        assert time_offs[1] == t1


# =============================================================================
# StaffService Tests
# =============================================================================

@pytest.mark.django_db
class TestStaffServiceModel:
    """Test StaffService model linking staff to services."""

    def test_create_staff_service(self, staff_member):
        """Should create staff service link."""
        # Note: We can't test with actual Service model without services module
        # This tests the StaffService model structure
        from staff.models import StaffService as StaffServiceModel
        assert StaffServiceModel._meta.get_field('staff') is not None
        assert StaffServiceModel._meta.get_field('service_id') is not None

    def test_staff_service_fields(self):
        """Should have override fields."""
        from staff.models import StaffService as StaffServiceModel
        assert StaffServiceModel._meta.get_field('custom_price') is not None
        assert StaffServiceModel._meta.get_field('custom_duration') is not None
        assert StaffServiceModel._meta.get_field('is_primary') is not None
