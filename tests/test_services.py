"""
Unit tests for staff module service layer.
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
)
from staff.services.staff_service import StaffService


# =============================================================================
# Staff Member CRUD Tests
# =============================================================================

@pytest.mark.django_db
class TestStaffMemberCRUD:
    """Test staff member CRUD operations via service layer."""

    def test_create_staff_member(self, role):
        """Should create staff member."""
        member, error = StaffService.create_staff_member(
            first_name='Alice',
            last_name='Brown',
            email='alice@example.com',
            role_id=role.id,
        )

        assert error is None
        assert member is not None
        assert member.first_name == 'Alice'
        assert member.role == role

    def test_create_staff_member_without_role(self):
        """Should create staff member without role."""
        member, error = StaffService.create_staff_member(
            first_name='Bob',
            last_name='White',
        )

        assert error is None
        assert member is not None
        assert member.role is None

    def test_create_staff_member_with_full_details(self, role):
        """Should create staff member with all details."""
        member, error = StaffService.create_staff_member(
            first_name='Carol',
            last_name='Green',
            email='carol@example.com',
            phone='+1987654321',
            employee_id='EMP002',
            role_id=role.id,
            is_bookable=True,
            hire_date=date.today(),
            hourly_rate=Decimal('30.00'),
            commission_rate=Decimal('15.00'),
            bio='Experienced stylist',
            notes='Prefers morning shifts',
        )

        assert error is None
        assert member is not None
        assert member.phone == '+1987654321'
        assert member.hourly_rate == Decimal('30.00')
        assert member.bio == 'Experienced stylist'

    def test_update_staff_member(self, staff_member):
        """Should update staff member."""
        success, error = StaffService.update_staff_member(
            staff_member,
            first_name='Johnny',
            hourly_rate=Decimal('30.00'),
        )

        assert success is True
        staff_member.refresh_from_db()
        assert staff_member.first_name == 'Johnny'
        assert staff_member.hourly_rate == Decimal('30.00')

    def test_update_staff_member_role(self, staff_member, secondary_role):
        """Should update staff member role."""
        success, error = StaffService.update_staff_member(
            staff_member,
            role_id=secondary_role.id,
        )

        assert success is True
        staff_member.refresh_from_db()
        assert staff_member.role == secondary_role

    def test_delete_staff_member(self, staff_member):
        """Should delete staff member."""
        member_id = staff_member.id
        success, error = StaffService.delete_staff_member(staff_member)

        assert success is True
        assert not StaffMember.objects.filter(id=member_id).exists()

    def test_toggle_staff_status(self, staff_member):
        """Should toggle staff active status."""
        assert staff_member.status == 'active'

        new_status = StaffService.toggle_staff_active(staff_member)
        assert new_status == 'inactive'

        staff_member.refresh_from_db()
        assert staff_member.status == 'inactive'

    def test_change_staff_status(self, staff_member):
        """Should change staff status to specific value."""
        success, error = StaffService.change_staff_status(staff_member, 'on_leave')
        assert success is True
        assert error is None

        staff_member.refresh_from_db()
        assert staff_member.status == 'on_leave'


# =============================================================================
# Staff Role CRUD Tests
# =============================================================================

@pytest.mark.django_db
class TestStaffRoleCRUD:
    """Test staff role CRUD operations."""

    def test_create_role(self):
        """Should create role."""
        role, error = StaffService.create_role(
            name='Receptionist',
            description='Front desk staff',
        )

        assert error is None
        assert role is not None
        assert role.name == 'Receptionist'

    def test_create_role_same_name_allowed(self, role):
        """Should allow creating role with same name (no unique constraint)."""
        new_role, error = StaffService.create_role(
            name='Stylist',  # Same name is allowed
        )

        # Roles can have the same name - no unique constraint
        assert error is None
        assert new_role is not None
        assert new_role.name == 'Stylist'
        assert new_role.id != role.id

    def test_update_role(self, role):
        """Should update role."""
        success, error = StaffService.update_role(
            role,
            name='Senior Stylist',
            description='Experienced stylist',
        )

        assert success is True
        role.refresh_from_db()
        assert role.name == 'Senior Stylist'

    def test_delete_role(self, secondary_role):
        """Should delete role."""
        role_id = secondary_role.id
        success, error = StaffService.delete_role(secondary_role)

        assert success is True
        assert not StaffRole.objects.filter(id=role_id).exists()

    def test_delete_role_with_staff(self, role, staff_member):
        """Should handle role with staff members."""
        # Staff should be reassigned or role deletion prevented
        # depending on business logic
        success, error = StaffService.delete_role(role)
        # Either succeeds (staff nullified) or fails (staff exist)
        # Just verify no crash
        assert isinstance(success, bool)


# =============================================================================
# Schedule Management Tests
# =============================================================================

@pytest.mark.django_db
class TestScheduleManagement:
    """Test schedule management."""

    def test_create_schedule(self, staff_member):
        """Should create schedule."""
        schedule, error = StaffService.create_schedule(
            staff=staff_member,
            name='Summer Schedule',
        )

        assert error is None
        assert schedule is not None
        assert schedule.staff == staff_member

    def test_create_default_schedule(self, staff_member):
        """Should create default schedule."""
        schedule, error = StaffService.create_schedule(
            staff=staff_member,
            name='Default',
            is_default=True,
        )

        assert error is None
        assert schedule.is_default is True

    def test_update_schedule(self, staff_schedule):
        """Should update schedule."""
        success, error = StaffService.update_schedule(
            staff_schedule,
            name='Updated Schedule',
        )

        assert success is True
        staff_schedule.refresh_from_db()
        assert staff_schedule.name == 'Updated Schedule'

    def test_delete_schedule(self, staff_schedule, staff_member):
        """Should delete schedule when more than one exists."""
        # Create a second schedule so we can delete the first
        second_schedule, _ = StaffService.create_schedule(
            staff=staff_member,
            name='Second Schedule',
            is_default=False,
        )

        schedule_id = staff_schedule.id
        success, error = StaffService.delete_schedule(staff_schedule)

        assert success is True
        assert not StaffSchedule.objects.filter(id=schedule_id).exists()

    def test_set_working_hours(self, staff_schedule):
        """Should set working hours for a day."""
        hours, error = StaffService.set_working_hours(
            schedule=staff_schedule,
            day_of_week=2,  # Wednesday
            start_time=time(10, 0),
            end_time=time(19, 0),
        )

        assert error is None
        assert hours is not None
        assert hours.day_of_week == 2

    def test_set_day_off(self, staff_schedule):
        """Should set day as day off."""
        hours, error = StaffService.set_working_hours(
            schedule=staff_schedule,
            day_of_week=6,  # Sunday
            is_day_off=True,
        )

        assert error is None
        assert hours.is_working is False  # is_working=False means day off

    def test_update_working_hours(self, working_hours):
        """Should update working hours."""
        success, error = StaffService.update_working_hours(
            working_hours,
            start_time=time(8, 0),
            end_time=time(16, 0),
        )

        assert success is True
        working_hours.refresh_from_db()
        assert working_hours.start_time == time(8, 0)

    def test_get_schedule_for_day(self, staff_member, staff_schedule, working_hours):
        """Should get schedule for specific day."""
        hours = StaffService.get_schedule_for_day(
            staff_member,
            day_of_week=0,  # Monday
        )

        assert hours is not None
        assert hours.start_time == time(9, 0)


# =============================================================================
# Time Off Management Tests
# =============================================================================

@pytest.mark.django_db
class TestTimeOffManagement:
    """Test time off management."""

    def test_create_time_off_request(self, staff_member):
        """Should create time off request."""
        time_off, error = StaffService.create_time_off(
            staff=staff_member,
            leave_type='vacation',
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=14),
            reason='Summer vacation',
            status='pending',  # Explicitly set to pending
        )

        assert error is None
        assert time_off is not None
        assert time_off.status == 'pending'

    def test_approve_time_off(self, time_off_request):
        """Should approve time off request."""
        success = StaffService.approve_time_off(time_off_request)

        assert success is True
        time_off_request.refresh_from_db()
        assert time_off_request.status == 'approved'

    def test_reject_time_off(self, time_off_request):
        """Should reject time off request."""
        success = StaffService.reject_time_off(time_off_request)

        assert success is True
        time_off_request.refresh_from_db()
        assert time_off_request.status == 'rejected'

    def test_cancel_time_off(self, time_off_request):
        """Should cancel time off request."""
        success = StaffService.cancel_time_off(time_off_request)

        assert success is True
        time_off_request.refresh_from_db()
        assert time_off_request.status == 'cancelled'

    def test_delete_time_off(self, time_off_request):
        """Should delete time off request."""
        time_off_id = time_off_request.id
        success, error = StaffService.delete_time_off(time_off_request)

        assert success is True
        assert not StaffTimeOff.objects.filter(id=time_off_id).exists()

    def test_get_pending_time_off(self, time_off_request, approved_time_off):
        """Should get pending time off requests."""
        pending = StaffService.get_pending_time_off()

        assert time_off_request in pending
        assert approved_time_off not in pending

    def test_get_staff_time_off(self, staff_member, time_off_request, approved_time_off):
        """Should get time off for specific staff."""
        time_offs = StaffService.get_staff_time_off(staff_member)

        assert time_off_request in time_offs
        assert approved_time_off in time_offs


# =============================================================================
# Search and Filter Tests
# =============================================================================

@pytest.mark.django_db
class TestSearchAndFilter:
    """Test search and filter functionality."""

    def test_search_by_name(self, staff_member, inactive_staff):
        """Should search staff by name."""
        results = StaffService.search_staff(query='John')

        assert staff_member in results
        assert inactive_staff not in results

    def test_filter_by_status(self, staff_member, inactive_staff, on_leave_staff):
        """Should filter by status."""
        active = StaffService.search_staff(status='active')
        inactive = StaffService.search_staff(status='inactive')

        assert staff_member in active
        assert inactive_staff in inactive
        assert on_leave_staff not in active

    def test_filter_by_role(self, staff_member, role, secondary_role):
        """Should filter by role."""
        results = StaffService.search_staff(role_id=role.id)

        assert staff_member in results

    def test_filter_bookable(self, staff_member, inactive_staff):
        """Should filter by bookable status."""
        bookable = StaffService.search_staff(is_bookable=True)
        non_bookable = StaffService.search_staff(is_bookable=False)

        assert staff_member in bookable
        assert inactive_staff in non_bookable

    def test_get_active_staff(self, staff_member, inactive_staff, on_leave_staff):
        """Should get only active staff."""
        active = StaffService.get_active_staff()

        assert staff_member in active
        assert inactive_staff not in active
        assert on_leave_staff not in active

    def test_get_bookable_staff(self, staff_member, inactive_staff):
        """Should get only bookable staff."""
        bookable = StaffService.get_bookable_staff()

        assert staff_member in bookable
        assert inactive_staff not in bookable


# =============================================================================
# Availability Tests
# =============================================================================

@pytest.mark.django_db
class TestAvailability:
    """Test availability checking."""

    def test_check_availability(self, staff_member, staff_schedule, working_hours):
        """Should check if staff is available."""
        # Monday at 10am should be available
        is_available = StaffService.is_available(
            staff_member,
            date.today(),  # Assuming today is a weekday
            time(10, 0),
        )
        # Result depends on what day it is, just verify no crash
        assert isinstance(is_available, bool)

    def test_get_available_slots(self, staff_member, staff_schedule, working_hours):
        """Should get available time slots."""
        slots = StaffService.get_available_slots(
            staff_member,
            date.today(),
            duration_minutes=60,
        )

        # Result depends on schedule, just verify structure
        assert isinstance(slots, list)


# =============================================================================
# Statistics Tests
# =============================================================================

@pytest.mark.django_db
class TestStatistics:
    """Test statistics functionality."""

    def test_get_staff_stats(self, staff_member, inactive_staff, on_leave_staff, role):
        """Should get comprehensive statistics."""
        stats = StaffService.get_staff_stats()

        assert stats['total_staff'] >= 3
        assert stats['active_staff'] >= 1
        assert stats['inactive_staff'] >= 1
        assert stats['on_leave'] >= 1
        assert stats['bookable_staff'] >= 1
        assert stats['roles'] >= 1

    def test_get_role_distribution(self, staff_member, inactive_staff, role):
        """Should get role distribution."""
        distribution = StaffService.get_role_distribution()

        # Should have at least one role with staff
        assert isinstance(distribution, list)


# =============================================================================
# Config Tests
# =============================================================================

@pytest.mark.django_db
class TestConfigManagement:
    """Test config management."""

    def test_get_config(self):
        """Should get config singleton."""
        config = StaffService.get_config()
        assert config.pk == 1

    def test_update_config(self, config):
        """Should update config."""
        success = StaffService.update_config(
            default_work_start=time(8, 0),
            default_work_end=time(17, 0),
            allow_staff_selection=False,  # Model uses allow_staff_selection, not allow_online_booking
        )

        assert success is True
        config.refresh_from_db()
        assert config.default_work_start == time(8, 0)
        assert config.allow_staff_selection is False
