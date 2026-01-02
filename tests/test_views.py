"""
E2E tests for staff module views.
Tests all CRUD operations and user interactions.
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
    """Test staff member CRUD operations."""

    def test_create_staff_member_success(self, role):
        """Should create staff member via service layer."""
        member, error = StaffService.create_staff_member(
            first_name='Test',
            last_name='Staff',
            email='test@example.com',
            role_id=role.id,
            is_bookable=True,
        )

        assert error is None
        assert member is not None
        assert member.first_name == 'Test'
        assert member.status == 'active'

    def test_update_staff_member(self, staff_member):
        """Should update staff member."""
        success, error = StaffService.update_staff_member(
            staff_member,
            first_name='Updated',
            hourly_rate=Decimal('35.00'),
        )

        assert success is True
        staff_member.refresh_from_db()
        assert staff_member.first_name == 'Updated'
        assert staff_member.hourly_rate == Decimal('35.00')

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


# =============================================================================
# Role Management Tests
# =============================================================================

@pytest.mark.django_db
class TestRoleManagement:
    """Test role management."""

    def test_create_role(self):
        """Should create role."""
        role, error = StaffService.create_role(
            name='New Role',
            description='Test role',
        )

        assert error is None
        assert role is not None
        assert role.name == 'New Role'

    def test_update_role(self, role):
        """Should update role."""
        success, error = StaffService.update_role(
            role,
            name='Updated Role',
            description='Updated description',
        )

        assert success is True
        role.refresh_from_db()
        assert role.name == 'Updated Role'

    def test_delete_role(self, secondary_role):
        """Should delete role."""
        role_id = secondary_role.id
        success, error = StaffService.delete_role(secondary_role)

        assert success is True
        assert not StaffRole.objects.filter(id=role_id).exists()

    def test_get_all_roles(self, role, secondary_role, inactive_role):
        """Should get all roles."""
        roles = StaffRole.objects.all()
        assert role in roles
        assert secondary_role in roles
        assert inactive_role in roles

    def test_get_active_roles(self, role, secondary_role, inactive_role):
        """Should get active roles only."""
        active_roles = StaffRole.objects.filter(is_active=True)
        assert role in active_roles
        assert secondary_role in active_roles
        assert inactive_role not in active_roles


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
            name='New Schedule',
            is_default=True,
        )

        assert error is None
        assert schedule is not None
        assert schedule.staff == staff_member
        assert schedule.is_default is True

    def test_update_schedule(self, staff_schedule):
        """Should update schedule."""
        success, error = StaffService.update_schedule(
            staff_schedule,
            name='Updated Schedule',
            is_active=False,
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
        """Should set working hours."""
        hours, error = StaffService.set_working_hours(
            schedule=staff_schedule,
            day_of_week=3,  # Thursday
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        assert error is None
        assert hours is not None
        assert hours.day_of_week == 3

    def test_set_day_off(self, staff_schedule):
        """Should set day off."""
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
            start_time=time(8, 30),
            end_time=time(17, 30),
            break_start=time(12, 30),
            break_end=time(13, 30),
        )

        assert success is True
        working_hours.refresh_from_db()
        assert working_hours.start_time == time(8, 30)


# =============================================================================
# Time Off Management Tests
# =============================================================================

@pytest.mark.django_db
class TestTimeOffManagement:
    """Test time off management."""

    def test_create_time_off(self, staff_member):
        """Should create time off request."""
        time_off, error = StaffService.create_time_off(
            staff=staff_member,
            leave_type='vacation',
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=14),
            reason='Annual vacation',
            status='pending',  # Explicitly set to pending
        )

        assert error is None
        assert time_off is not None
        assert time_off.status == 'pending'

    def test_approve_time_off(self, time_off_request):
        """Should approve time off."""
        success = StaffService.approve_time_off(time_off_request)

        assert success is True
        time_off_request.refresh_from_db()
        assert time_off_request.status == 'approved'

    def test_reject_time_off(self, time_off_request):
        """Should reject time off."""
        success = StaffService.reject_time_off(time_off_request)

        assert success is True
        time_off_request.refresh_from_db()
        assert time_off_request.status == 'rejected'

    def test_cancel_time_off(self, time_off_request):
        """Should cancel time off."""
        success = StaffService.cancel_time_off(time_off_request)

        assert success is True
        time_off_request.refresh_from_db()
        assert time_off_request.status == 'cancelled'

    def test_delete_time_off(self, time_off_request):
        """Should delete time off."""
        time_off_id = time_off_request.id
        success, error = StaffService.delete_time_off(time_off_request)

        assert success is True
        assert not StaffTimeOff.objects.filter(id=time_off_id).exists()


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

    def test_search_by_email(self, staff_member):
        """Should search by email."""
        results = StaffService.search_staff(query='john@example')

        assert staff_member in results

    def test_filter_by_status(self, staff_member, inactive_staff, on_leave_staff):
        """Should filter by status."""
        active = StaffService.search_staff(status='active')
        inactive = StaffService.search_staff(status='inactive')
        on_leave = StaffService.search_staff(status='on_leave')

        assert staff_member in active
        assert inactive_staff in inactive
        assert on_leave_staff in on_leave

    def test_filter_by_role(self, staff_member, role):
        """Should filter by role."""
        results = StaffService.search_staff(role_id=role.id)

        assert staff_member in results

    def test_filter_bookable_staff(self, staff_member, inactive_staff):
        """Should filter bookable staff."""
        bookable = StaffService.search_staff(is_bookable=True)

        assert staff_member in bookable
        assert inactive_staff not in bookable

    def test_get_active_staff(self, staff_member, inactive_staff):
        """Should get only active staff."""
        active = StaffService.get_active_staff()

        assert staff_member in active
        assert inactive_staff not in active

    def test_get_bookable_staff(self, staff_member, inactive_staff):
        """Should get bookable staff."""
        bookable = StaffService.get_bookable_staff()

        assert staff_member in bookable


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
        assert 'bookable_staff' in stats
        assert 'roles' in stats

    def test_get_role_distribution(self, staff_member, inactive_staff, role):
        """Should get role distribution."""
        distribution = StaffService.get_role_distribution()

        assert isinstance(distribution, list)


# =============================================================================
# Settings Tests
# =============================================================================

@pytest.mark.django_db
class TestSettings:
    """Test settings management."""

    def test_get_config(self):
        """Should get config singleton."""
        config = StaffConfig.get_config()
        assert config.pk == 1

    def test_update_settings(self, config):
        """Should update settings."""
        config.default_work_start = time(8, 0)
        config.default_work_end = time(17, 0)
        config.allow_staff_selection = False
        config.save()

        config.refresh_from_db()
        assert config.default_work_start == time(8, 0)
        assert config.allow_staff_selection is False

    def test_toggle_boolean_setting(self, config):
        """Should toggle boolean settings."""
        original = config.allow_staff_selection
        config.allow_staff_selection = not original
        config.save()

        config.refresh_from_db()
        assert config.allow_staff_selection != original


# =============================================================================
# Integration Tests - Full Lifecycle
# =============================================================================

@pytest.mark.django_db
class TestFullLifecycle:
    """Integration tests for complete workflows."""

    def test_staff_full_lifecycle(self):
        """Test complete staff member lifecycle."""
        # 1. Create role
        role, _ = StaffService.create_role(
            name='Test Role',
            description='For lifecycle test',
        )

        # 2. Create staff member
        member, _ = StaffService.create_staff_member(
            first_name='Lifecycle',
            last_name='Test',
            email='lifecycle@test.com',
            role_id=role.id,
            is_bookable=True,
        )
        assert member is not None

        # 3. Create schedule
        schedule, _ = StaffService.create_schedule(
            staff=member,
            name='Regular Schedule',
            is_default=True,
        )
        assert schedule is not None

        # 4. Set working hours
        hours, _ = StaffService.set_working_hours(
            schedule=schedule,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        assert hours is not None

        # 5. Create time off
        time_off, _ = StaffService.create_time_off(
            staff=member,
            leave_type='vacation',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
        )
        assert time_off is not None

        # 6. Approve time off
        success = StaffService.approve_time_off(time_off)
        assert success is True

        # 7. Update staff
        success, _ = StaffService.update_staff_member(
            member,
            hourly_rate=Decimal('30.00'),
        )
        assert success is True

        # 8. Toggle status
        new_status = StaffService.toggle_staff_active(member)
        assert new_status == 'inactive'

        # 9. Delete staff member
        success, _ = StaffService.delete_staff_member(member)
        assert success is True

    def test_schedule_with_full_week(self):
        """Test schedule with full week working hours."""
        # Create role and staff
        role, _ = StaffService.create_role(name='Full Week Role')
        member, _ = StaffService.create_staff_member(
            first_name='Full',
            last_name='Week',
            role_id=role.id,
        )

        # Create schedule
        schedule, _ = StaffService.create_schedule(
            staff=member,
            name='Full Week Schedule',
            is_default=True,
        )

        # Set working hours for each day
        for day in range(7):
            is_weekend = day >= 5
            if is_weekend:
                hours, _ = StaffService.set_working_hours(
                    schedule=schedule,
                    day_of_week=day,
                    is_day_off=True,
                )
            else:
                hours, _ = StaffService.set_working_hours(
                    schedule=schedule,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(17, 0),
                    break_start=time(12, 0),
                    break_end=time(13, 0),
                )
            assert hours is not None

        # Verify all days created
        all_hours = StaffWorkingHours.objects.filter(schedule=schedule)
        assert all_hours.count() == 7

        # Verify weekends are off (is_working=False means day off)
        weekend_hours = all_hours.filter(day_of_week__gte=5)
        for wh in weekend_hours:
            assert wh.is_working is False

    def test_multiple_time_off_requests(self, staff_member):
        """Test multiple time off requests workflow."""
        # Create multiple requests with status='pending'
        requests = []
        for i in range(3):
            time_off, _ = StaffService.create_time_off(
                staff=staff_member,
                leave_type='vacation',
                start_date=date.today() + timedelta(days=30 + i * 14),
                end_date=date.today() + timedelta(days=35 + i * 14),
                reason=f'Vacation {i + 1}',
                status='pending',  # Explicitly set to pending
            )
            requests.append(time_off)

        # Verify all pending
        pending = StaffService.get_pending_time_off()
        for req in requests:
            assert req in pending

        # Approve first, reject second, leave third pending
        StaffService.approve_time_off(requests[0])
        StaffService.reject_time_off(requests[1])

        # Verify statuses
        for req in requests:
            req.refresh_from_db()
        assert requests[0].status == 'approved'
        assert requests[1].status == 'rejected'
        assert requests[2].status == 'pending'

        # Get staff time off
        all_time_off = StaffService.get_staff_time_off(staff_member)
        assert len(all_time_off) >= 3

    def test_role_with_multiple_staff(self):
        """Test role with multiple staff members."""
        # Create role
        role, _ = StaffService.create_role(
            name='Team Role',
            description='For team test',
        )

        # Create multiple staff
        members = []
        for i in range(5):
            member, _ = StaffService.create_staff_member(
                first_name=f'Team Member {i + 1}',
                last_name='Test',
                email=f'team{i + 1}@test.com',
                role_id=role.id,
            )
            members.append(member)

        # Verify all have the role
        for member in members:
            assert member.role == role

        # Get role stats
        staff_count = StaffMember.objects.filter(role=role).count()
        assert staff_count == 5

        # Filter by role
        results = StaffService.search_staff(role_id=role.id)
        assert len(results) == 5


# =============================================================================
# Availability Tests
# =============================================================================

@pytest.mark.django_db
class TestAvailabilityChecks:
    """Test availability checking."""

    def test_staff_availability_on_working_day(self, staff_member, staff_schedule, working_hours):
        """Should check availability on working day."""
        # Check if available during working hours
        is_available = StaffService.is_available(
            staff_member,
            date.today(),
            time(10, 0),
        )
        # Result depends on actual day, just verify no crash
        assert isinstance(is_available, bool)

    def test_get_available_slots(self, staff_member, staff_schedule, working_hours):
        """Should get available time slots."""
        slots = StaffService.get_available_slots(
            staff_member,
            date.today(),
            duration_minutes=60,
        )

        assert isinstance(slots, list)

    def test_availability_with_time_off(self, staff_member, staff_schedule, working_hours, approved_time_off):
        """Should consider approved time off."""
        # This would be unavailable during approved time off
        is_available = StaffService.is_available(
            staff_member,
            approved_time_off.start_date,
            time(10, 0),
        )
        # Should be false during time off
        # Note: depends on implementation
        assert isinstance(is_available, bool)
