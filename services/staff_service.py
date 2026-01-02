"""
Service layer for the staff module.
Handles all business logic for staff members, schedules, and availability.
"""
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, date, time, timedelta
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.utils import timezone

from staff.models import (
    StaffConfig,
    StaffRole,
    StaffMember,
    StaffSchedule,
    StaffWorkingHours,
    StaffTimeOff,
    StaffService as StaffServiceModel,
)


class StaffService:
    """Service class for managing staff members and schedules."""

    # =========================================================================
    # Staff Member CRUD
    # =========================================================================

    @staticmethod
    @transaction.atomic
    def create_staff_member(
        first_name: str,
        last_name: str,
        email: str = '',
        phone: str = '',
        role_id: Optional[int] = None,
        employee_id: Optional[str] = None,
        hire_date: Optional[date] = None,
        bio: str = '',
        specialties: str = '',
        is_bookable: bool = True,
        hourly_rate: Decimal = Decimal('0.00'),
        commission_rate: Decimal = Decimal('0.00'),
        color: str = '',
        booking_buffer: int = 0,
        user_id: Optional[int] = None,
        notes: str = '',
    ) -> Tuple[Optional[StaffMember], Optional[str]]:
        """
        Create a new staff member.

        Returns:
            Tuple of (staff_member, error_message)
        """
        if not first_name or not first_name.strip():
            return None, "First name is required"

        # Validate role
        role = None
        if role_id:
            try:
                role = StaffRole.objects.get(pk=role_id)
            except StaffRole.DoesNotExist:
                return None, "Role not found"

        # Generate unique employee ID if not provided
        if not employee_id:
            last_id = StaffMember.objects.order_by('-id').first()
            next_num = (last_id.id + 1) if last_id else 1
            employee_id = f"EMP-{next_num:04d}"

        try:
            staff = StaffMember.objects.create(
                first_name=first_name.strip(),
                last_name=last_name.strip() if last_name else '',
                email=email,
                phone=phone,
                role=role,
                employee_id=employee_id,
                hire_date=hire_date,
                bio=bio,
                specialties=specialties,
                is_bookable=is_bookable,
                hourly_rate=hourly_rate,
                commission_rate=commission_rate,
                color=color,
                booking_buffer=booking_buffer,
                user_id=user_id,
                notes=notes,
            )

            # Create default schedule
            StaffService._create_default_schedule(staff)

            return staff, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def _create_default_schedule(staff: StaffMember):
        """Create default working schedule for new staff."""
        config = StaffConfig.get_config()

        schedule = StaffSchedule.objects.create(
            staff=staff,
            name="Default Schedule",
            is_default=True,
        )

        # Create Monday-Friday working hours
        for day in range(5):
            StaffWorkingHours.objects.create(
                schedule=schedule,
                day_of_week=day,
                start_time=config.default_work_start,
                end_time=config.default_work_end,
                is_working=True,
            )

        # Create weekend as day off
        for day in [5, 6]:
            StaffWorkingHours.objects.create(
                schedule=schedule,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(18, 0),
                is_working=False,
            )

    @staticmethod
    @transaction.atomic
    def update_staff_member(
        staff: StaffMember,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """Update an existing staff member."""
        try:
            # Handle role update
            if 'role_id' in kwargs:
                role_id = kwargs.pop('role_id')
                if role_id:
                    try:
                        kwargs['role'] = StaffRole.objects.get(pk=role_id)
                    except StaffRole.DoesNotExist:
                        return False, "Role not found"
                else:
                    kwargs['role'] = None

            for key, value in kwargs.items():
                if hasattr(staff, key):
                    setattr(staff, key, value)

            staff.save()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_staff_member(staff: StaffMember) -> Tuple[bool, Optional[str]]:
        """Delete a staff member."""
        try:
            staff.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def toggle_staff_bookable(staff: StaffMember) -> bool:
        """Toggle staff bookable status."""
        staff.is_bookable = not staff.is_bookable
        staff.save(update_fields=['is_bookable', 'updated_at'])
        return staff.is_bookable

    @staticmethod
    def change_staff_status(
        staff: StaffMember,
        new_status: str
    ) -> Tuple[bool, Optional[str]]:
        """Change staff status."""
        valid_statuses = ['active', 'inactive', 'on_leave', 'terminated']
        if new_status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        staff.status = new_status
        if new_status == 'terminated':
            staff.termination_date = date.today()
            staff.is_bookable = False

        staff.save()
        return True, None

    # =========================================================================
    # Role Management
    # =========================================================================

    @staticmethod
    def create_role(
        name: str,
        description: str = '',
        color: str = '',
        order: int = 0,
    ) -> Tuple[Optional[StaffRole], Optional[str]]:
        """Create a staff role."""
        if not name or not name.strip():
            return None, "Role name is required"

        try:
            role = StaffRole.objects.create(
                name=name.strip(),
                description=description,
                color=color,
                order=order,
            )
            return role, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def update_role(
        role: StaffRole,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """Update a role."""
        try:
            for key, value in kwargs.items():
                if hasattr(role, key):
                    setattr(role, key, value)
            role.save()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_role(role: StaffRole) -> Tuple[bool, Optional[str]]:
        """Delete a role."""
        try:
            role.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # Schedule Management
    # =========================================================================

    @staticmethod
    def create_schedule(
        staff: StaffMember,
        name: str = "New Schedule",
        is_default: bool = False,
        effective_from: Optional[date] = None,
        effective_until: Optional[date] = None,
    ) -> Tuple[Optional[StaffSchedule], Optional[str]]:
        """Create a new schedule for staff member."""
        try:
            schedule = StaffSchedule.objects.create(
                staff=staff,
                name=name,
                is_default=is_default,
                effective_from=effective_from,
                effective_until=effective_until,
            )
            return schedule, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def update_schedule(
        schedule: StaffSchedule,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """Update a schedule."""
        try:
            for key, value in kwargs.items():
                if hasattr(schedule, key):
                    setattr(schedule, key, value)
            schedule.save()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_schedule(schedule: StaffSchedule) -> Tuple[bool, Optional[str]]:
        """Delete a schedule."""
        # Don't delete the last schedule
        if schedule.staff.schedules.count() <= 1:
            return False, "Cannot delete the last schedule"

        try:
            # If deleting default, make another schedule default
            if schedule.is_default:
                other = schedule.staff.schedules.exclude(pk=schedule.pk).first()
                if other:
                    other.is_default = True
                    other.save()

            schedule.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    @transaction.atomic
    def save_working_hours(
        schedule: StaffSchedule,
        hours_data: List[Dict]
    ) -> Tuple[bool, Optional[str]]:
        """
        Save working hours for a schedule.

        Args:
            schedule: The schedule to update
            hours_data: List of dicts with day_of_week, start_time, end_time, etc.
        """
        try:
            # Delete existing hours
            schedule.working_hours.all().delete()

            # Create new hours
            for data in hours_data:
                day = data.get('day_of_week')
                if day is None:
                    continue

                StaffWorkingHours.objects.create(
                    schedule=schedule,
                    day_of_week=int(day),
                    start_time=data.get('start_time', time(9, 0)),
                    end_time=data.get('end_time', time(18, 0)),
                    break_start=data.get('break_start'),
                    break_end=data.get('break_end'),
                    is_working=data.get('is_working', True),
                )

            return True, None
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # Time Off Management
    # =========================================================================

    @staticmethod
    def create_time_off(
        staff: StaffMember,
        start_date: date,
        end_date: date,
        leave_type: str = 'vacation',
        reason: str = '',
        is_full_day: bool = True,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        status: str = 'approved',
    ) -> Tuple[Optional[StaffTimeOff], Optional[str]]:
        """Create time off request."""
        if end_date < start_date:
            return None, "End date must be after start date"

        try:
            time_off = StaffTimeOff.objects.create(
                staff=staff,
                start_date=start_date,
                end_date=end_date,
                leave_type=leave_type,
                reason=reason,
                is_full_day=is_full_day,
                start_time=start_time,
                end_time=end_time,
                status=status,
            )
            return time_off, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def update_time_off(
        time_off: StaffTimeOff,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """Update time off request."""
        try:
            if 'start_date' in kwargs and 'end_date' in kwargs:
                if kwargs['end_date'] < kwargs['start_date']:
                    return False, "End date must be after start date"

            for key, value in kwargs.items():
                if hasattr(time_off, key):
                    setattr(time_off, key, value)

            time_off.save()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def approve_time_off(
        time_off: StaffTimeOff,
        approved_by_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Approve time off request."""
        time_off.status = 'approved'
        time_off.approved_by_id = approved_by_id
        time_off.approved_at = timezone.now()
        time_off.save()
        return True, None

    @staticmethod
    def reject_time_off(
        time_off: StaffTimeOff,
        reason: str = ''
    ) -> Tuple[bool, Optional[str]]:
        """Reject time off request."""
        time_off.status = 'rejected'
        if reason:
            time_off.notes = reason
        time_off.save()
        return True, None

    @staticmethod
    def delete_time_off(time_off: StaffTimeOff) -> Tuple[bool, Optional[str]]:
        """Delete time off request."""
        try:
            time_off.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # Staff Services Management
    # =========================================================================

    @staticmethod
    @transaction.atomic
    def assign_services(
        staff: StaffMember,
        service_data: List[Dict]
    ) -> Tuple[bool, Optional[str]]:
        """
        Assign services to staff member.

        Args:
            staff: Staff member
            service_data: List of dicts with service_id, service_name, custom_duration, etc.
        """
        try:
            # Get existing service IDs to preserve
            existing = {s.service_id: s for s in staff.staff_services.all()}

            for data in service_data:
                service_id = data.get('service_id')
                if not service_id:
                    continue

                if service_id in existing:
                    # Update existing
                    ss = existing[service_id]
                    ss.custom_duration = data.get('custom_duration')
                    ss.custom_price = data.get('custom_price')
                    ss.is_primary = data.get('is_primary', False)
                    ss.is_active = data.get('is_active', True)
                    ss.save()
                    del existing[service_id]
                else:
                    # Create new
                    StaffServiceModel.objects.create(
                        staff=staff,
                        service_id=service_id,
                        service_name=data.get('service_name', 'Unknown'),
                        custom_duration=data.get('custom_duration'),
                        custom_price=data.get('custom_price'),
                        is_primary=data.get('is_primary', False),
                        is_active=data.get('is_active', True),
                    )

            # Deactivate removed services
            for ss in existing.values():
                ss.is_active = False
                ss.save()

            return True, None
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # Availability Checking
    # =========================================================================

    @staticmethod
    def get_staff_schedule_for_date(
        staff: StaffMember,
        target_date: date
    ) -> Optional[StaffWorkingHours]:
        """Get working hours for staff on a specific date."""
        # Find applicable schedule
        schedules = staff.schedules.filter(is_active=True)

        # Check for date-specific schedules first
        for schedule in schedules:
            if schedule.is_applicable_on(target_date):
                day_of_week = target_date.weekday()
                try:
                    return schedule.working_hours.get(day_of_week=day_of_week)
                except StaffWorkingHours.DoesNotExist:
                    continue

        # Fall back to default schedule
        default = schedules.filter(is_default=True).first()
        if default:
            day_of_week = target_date.weekday()
            try:
                return default.working_hours.get(day_of_week=day_of_week)
            except StaffWorkingHours.DoesNotExist:
                pass

        return None

    @staticmethod
    def is_staff_available_at(
        staff: StaffMember,
        target_datetime: datetime
    ) -> bool:
        """Check if staff is available at specific datetime."""
        if staff.status != 'active':
            return False

        target_date = target_datetime.date()
        target_time = target_datetime.time()

        # Check time off
        time_off = staff.time_off.filter(
            status='approved',
            start_date__lte=target_date,
            end_date__gte=target_date,
        )
        for to in time_off:
            if to.is_full_day:
                return False
            if to.start_time and to.end_time:
                if to.start_time <= target_time <= to.end_time:
                    return False

        # Check working hours
        hours = StaffService.get_staff_schedule_for_date(staff, target_date)
        if not hours or not hours.is_working:
            return False

        # Check if within working hours
        if target_time < hours.start_time or target_time >= hours.end_time:
            return False

        # Check break time
        if hours.break_start and hours.break_end:
            if hours.break_start <= target_time < hours.break_end:
                return False

        return True

    @staticmethod
    def get_available_staff(
        target_datetime: datetime,
        service_id: Optional[int] = None
    ) -> List[StaffMember]:
        """Get all available staff at a specific datetime."""
        available = []

        staff_qs = StaffMember.objects.filter(
            status='active',
            is_bookable=True,
        )

        if service_id:
            staff_qs = staff_qs.filter(
                staff_services__service_id=service_id,
                staff_services__is_active=True,
            )

        for staff in staff_qs:
            if StaffService.is_staff_available_at(staff, target_datetime):
                available.append(staff)

        return available

    @staticmethod
    def get_available_slots(
        staff: StaffMember,
        target_date: date,
        duration_minutes: int = 60,
        slot_interval: int = 15,
    ) -> List[time]:
        """Get available time slots for a staff member on a date."""
        slots = []

        hours = StaffService.get_staff_schedule_for_date(staff, target_date)
        if not hours or not hours.is_working:
            return slots

        # Check time off
        time_off = staff.time_off.filter(
            status='approved',
            start_date__lte=target_date,
            end_date__gte=target_date,
            is_full_day=True,
        ).exists()
        if time_off:
            return slots

        # Generate slots
        current = datetime.combine(target_date, hours.start_time)
        end = datetime.combine(target_date, hours.end_time)

        while current + timedelta(minutes=duration_minutes) <= end:
            slot_time = current.time()

            # Skip break time
            if hours.break_start and hours.break_end:
                slot_end = (current + timedelta(minutes=duration_minutes)).time()
                if not (slot_end <= hours.break_start or slot_time >= hours.break_end):
                    current += timedelta(minutes=slot_interval)
                    continue

            slots.append(slot_time)
            current += timedelta(minutes=slot_interval)

        return slots

    # =========================================================================
    # Query Methods
    # =========================================================================

    @staticmethod
    def search_staff(
        query: str = '',
        role_id: Optional[int] = None,
        status: Optional[str] = None,
        is_bookable: Optional[bool] = None,
        ordering: str = 'first_name',
    ) -> List[StaffMember]:
        """Search and filter staff members."""
        queryset = StaffMember.objects.all()

        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query) |
                Q(employee_id__icontains=query)
            )

        if role_id:
            queryset = queryset.filter(role_id=role_id)

        if status:
            queryset = queryset.filter(status=status)

        if is_bookable is not None:
            queryset = queryset.filter(is_bookable=is_bookable)

        return queryset.order_by(ordering)

    @staticmethod
    def get_bookable_staff() -> List[StaffMember]:
        """Get all bookable staff members."""
        return StaffMember.objects.filter(
            status='active',
            is_bookable=True,
        ).order_by('order', 'first_name')

    @staticmethod
    def get_staff_for_service(service_id: int) -> List[StaffMember]:
        """Get staff members who can provide a service."""
        return StaffMember.objects.filter(
            status='active',
            is_bookable=True,
            staff_services__service_id=service_id,
            staff_services__is_active=True,
        ).distinct().order_by('order', 'first_name')

    # =========================================================================
    # Statistics
    # =========================================================================

    @staticmethod
    def get_staff_stats() -> Dict[str, Any]:
        """Get staff statistics."""
        staff = StaffMember.objects.all()

        return {
            'total_staff': staff.count(),
            'active_staff': staff.filter(status='active').count(),
            'inactive_staff': staff.filter(status='inactive').count(),
            'on_leave': staff.filter(status='on_leave').count(),
            'terminated': staff.filter(status='terminated').count(),
            'bookable_staff': staff.filter(status='active', is_bookable=True).count(),
            'roles': StaffRole.objects.filter(is_active=True).count(),
            'pending_time_off': StaffTimeOff.objects.filter(status='pending').count(),
            'avg_hourly_rate': staff.filter(status='active').aggregate(
                avg=Avg('hourly_rate')
            )['avg'] or Decimal('0'),
            'avg_commission_rate': staff.filter(status='active').aggregate(
                avg=Avg('commission_rate')
            )['avg'] or Decimal('0'),
        }

    @staticmethod
    def get_staff_schedule_summary(staff: StaffMember) -> Dict[str, Any]:
        """Get schedule summary for a staff member."""
        default_schedule = staff.schedules.filter(is_default=True).first()

        if not default_schedule:
            return {
                'has_schedule': False,
                'weekly_hours': 0,
                'working_days': [],
            }

        hours = default_schedule.working_hours.filter(is_working=True)
        working_days = [h.day_of_week for h in hours]
        weekly_minutes = sum(h.working_minutes for h in hours)

        return {
            'has_schedule': True,
            'weekly_hours': weekly_minutes // 60,
            'weekly_minutes': weekly_minutes % 60,
            'working_days': working_days,
            'days_off': [d for d in range(7) if d not in working_days],
        }

    # =========================================================================
    # Additional Methods Required by Tests
    # =========================================================================

    @staticmethod
    def toggle_staff_active(staff: StaffMember) -> str:
        """Toggle staff active/inactive status."""
        if staff.status == 'active':
            staff.status = 'inactive'
        else:
            staff.status = 'active'
        staff.save(update_fields=['status', 'updated_at'])
        return staff.status

    @staticmethod
    def get_active_staff() -> List[StaffMember]:
        """Get all active staff members."""
        return list(StaffMember.objects.filter(status='active'))

    @staticmethod
    def set_working_hours(
        schedule: StaffSchedule,
        day_of_week: int,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        break_start: Optional[time] = None,
        break_end: Optional[time] = None,
        is_day_off: bool = False,
    ) -> Tuple[Optional[StaffWorkingHours], Optional[str]]:
        """Set working hours for a specific day."""
        try:
            # Check if hours exist for this day
            hours, created = StaffWorkingHours.objects.update_or_create(
                schedule=schedule,
                day_of_week=day_of_week,
                defaults={
                    'start_time': start_time or time(9, 0),
                    'end_time': end_time or time(18, 0),
                    'break_start': break_start,
                    'break_end': break_end,
                    'is_working': not is_day_off,
                }
            )
            return hours, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def update_working_hours(
        hours: StaffWorkingHours,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """Update existing working hours."""
        try:
            # Handle is_day_off -> is_working conversion
            if 'is_day_off' in kwargs:
                kwargs['is_working'] = not kwargs.pop('is_day_off')

            for key, value in kwargs.items():
                if hasattr(hours, key):
                    setattr(hours, key, value)
            hours.save()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_schedule_for_day(
        staff: StaffMember,
        day_of_week: int,
    ) -> Optional[StaffWorkingHours]:
        """Get working hours for a specific day of week."""
        default_schedule = staff.schedules.filter(is_default=True, is_active=True).first()
        if not default_schedule:
            return None
        try:
            return default_schedule.working_hours.get(day_of_week=day_of_week)
        except StaffWorkingHours.DoesNotExist:
            return None

    @staticmethod
    def approve_time_off(time_off: StaffTimeOff, approved_by_id: int = None) -> bool:
        """Approve time off request."""
        time_off.status = 'approved'
        if approved_by_id:
            time_off.approved_by_id = approved_by_id
        time_off.approved_at = timezone.now()
        time_off.save()
        return True

    @staticmethod
    def reject_time_off(time_off: StaffTimeOff, reason: str = '') -> bool:
        """Reject time off request."""
        time_off.status = 'rejected'
        if reason:
            time_off.notes = reason
        time_off.save()
        return True

    @staticmethod
    def cancel_time_off(time_off: StaffTimeOff) -> bool:
        """Cancel time off request."""
        time_off.status = 'cancelled'
        time_off.save()
        return True

    @staticmethod
    def get_pending_time_off() -> List[StaffTimeOff]:
        """Get all pending time off requests."""
        return list(StaffTimeOff.objects.filter(status='pending'))

    @staticmethod
    def get_staff_time_off(staff: StaffMember) -> List[StaffTimeOff]:
        """Get all time off for a staff member."""
        return list(staff.time_off.all())

    @staticmethod
    def is_available(
        staff: StaffMember,
        target_date: date,
        target_time: time,
    ) -> bool:
        """Check if staff is available at a specific date and time."""
        if staff.status != 'active':
            return False

        # Check time off
        time_off_entries = staff.time_off.filter(
            status='approved',
            start_date__lte=target_date,
            end_date__gte=target_date,
        )
        for to in time_off_entries:
            if to.is_full_day:
                return False
            if to.start_time and to.end_time:
                if to.start_time <= target_time <= to.end_time:
                    return False

        # Check working hours
        hours = StaffService.get_schedule_for_day(staff, target_date.weekday())
        if not hours or not hours.is_working:
            return False

        # Check if within working hours
        if target_time < hours.start_time or target_time >= hours.end_time:
            return False

        # Check break time
        if hours.break_start and hours.break_end:
            if hours.break_start <= target_time < hours.break_end:
                return False

        return True

    @staticmethod
    def get_config() -> StaffConfig:
        """Get staff config singleton."""
        return StaffConfig.get_config()

    @staticmethod
    def update_config(**kwargs) -> bool:
        """Update staff config."""
        config = StaffConfig.get_config()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        config.save()
        return True

    @staticmethod
    def get_role_distribution() -> List[Dict]:
        """Get role distribution statistics."""
        roles = StaffRole.objects.filter(is_active=True).annotate(
            staff_count=Count('members')
        )
        return [
            {'id': r.id, 'name': r.name, 'count': r.staff_count}
            for r in roles
        ]
