"""
Views for the staff module.
"""
import json
from datetime import datetime, date, time
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Q

from apps.accounts.decorators import login_required
from apps.modules_runtime.decorators import module_view

from .models import (
    StaffConfig,
    StaffRole,
    StaffMember,
    StaffSchedule,
    StaffWorkingHours,
    StaffTimeOff,
    StaffService as StaffServiceModel,
)
from .services import StaffServiceLayer


# =============================================================================
# Dashboard
# =============================================================================

@login_required
@module_view("staff", "dashboard")
def dashboard(request):
    """Staff dashboard with statistics."""
    stats = StaffServiceLayer.get_staff_stats()
    recent_staff = StaffMember.objects.filter(status='active').order_by('-created_at')[:5]
    pending_time_off = StaffTimeOff.objects.filter(status='pending').order_by('start_date')[:5]

    return {
        'stats': stats,
        'recent_staff': recent_staff,
        'pending_time_off': pending_time_off,
    }


# =============================================================================
# Staff CRUD
# =============================================================================

@login_required
@module_view("staff", "list")
def staff_list(request):
    """List all staff members."""
    search = request.GET.get('search', '')
    role_id = request.GET.get('role')
    status = request.GET.get('status', 'active')

    staff_members = StaffServiceLayer.search_staff(
        query=search,
        role_id=int(role_id) if role_id else None,
        status=status if status != 'all' else None,
    )

    roles = StaffRole.objects.filter(is_active=True).order_by('name')

    return {
        'staff_members': staff_members,
        'roles': roles,
        'search': search,
        'selected_role': role_id,
        'status': status,
    }


@login_required
def staff_create(request):
    """Create a new staff member."""
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            hire_date = None
            if data.get('hire_date'):
                hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()

            staff, error = StaffServiceLayer.create_staff_member(
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                email=data.get('email', ''),
                phone=data.get('phone', ''),
                role_id=int(data['role_id']) if data.get('role_id') else None,
                hire_date=hire_date,
                bio=data.get('bio', ''),
                specialties=data.get('specialties', ''),
                is_bookable=data.get('is_bookable', 'true') in ['true', True, '1', 1],
                hourly_rate=Decimal(data.get('hourly_rate', '0')),
                commission_rate=Decimal(data.get('commission_rate', '0')),
                color=data.get('color', ''),
                booking_buffer=int(data.get('booking_buffer', 0)),
                notes=data.get('notes', ''),
            )

            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True, 'id': staff.id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    roles = StaffRole.objects.filter(is_active=True).order_by('name')

    return render(request, 'staff/staff_form.html', {
        'mode': 'create',
        'roles': roles,
    })


@login_required
def staff_detail(request, pk):
    """Staff member detail view."""
    staff = get_object_or_404(StaffMember, pk=pk)
    schedule_summary = StaffServiceLayer.get_staff_schedule_summary(staff)
    services = staff.staff_services.filter(is_active=True)
    recent_time_off = staff.time_off.order_by('-start_date')[:5]

    return render(request, 'staff/staff_detail.html', {
        'staff': staff,
        'schedule_summary': schedule_summary,
        'services': services,
        'recent_time_off': recent_time_off,
    })


@login_required
def staff_edit(request, pk):
    """Edit a staff member."""
    staff = get_object_or_404(StaffMember, pk=pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            kwargs = {}
            if 'first_name' in data:
                kwargs['first_name'] = data['first_name']
            if 'last_name' in data:
                kwargs['last_name'] = data['last_name']
            if 'email' in data:
                kwargs['email'] = data['email']
            if 'phone' in data:
                kwargs['phone'] = data['phone']
            if 'role_id' in data:
                kwargs['role_id'] = int(data['role_id']) if data['role_id'] else None
            if 'bio' in data:
                kwargs['bio'] = data['bio']
            if 'specialties' in data:
                kwargs['specialties'] = data['specialties']
            if 'is_bookable' in data:
                kwargs['is_bookable'] = data['is_bookable'] in ['true', True, '1', 1]
            if 'hourly_rate' in data:
                kwargs['hourly_rate'] = Decimal(data['hourly_rate'])
            if 'commission_rate' in data:
                kwargs['commission_rate'] = Decimal(data['commission_rate'])
            if 'color' in data:
                kwargs['color'] = data['color']
            if 'booking_buffer' in data:
                kwargs['booking_buffer'] = int(data['booking_buffer'])
            if 'notes' in data:
                kwargs['notes'] = data['notes']
            if 'status' in data:
                kwargs['status'] = data['status']
            if 'hire_date' in data and data['hire_date']:
                kwargs['hire_date'] = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()

            success, error = StaffServiceLayer.update_staff_member(staff, **kwargs)

            if not success:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    roles = StaffRole.objects.filter(is_active=True).order_by('name')

    return render(request, 'staff/staff_form.html', {
        'mode': 'edit',
        'staff': staff,
        'roles': roles,
    })


@login_required
@require_POST
def staff_delete(request, pk):
    """Delete a staff member."""
    staff = get_object_or_404(StaffMember, pk=pk)
    success, error = StaffServiceLayer.delete_staff_member(staff)

    if not success:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True})


@login_required
@require_POST
def staff_toggle(request, pk):
    """Toggle staff bookable status."""
    staff = get_object_or_404(StaffMember, pk=pk)
    is_bookable = StaffServiceLayer.toggle_staff_bookable(staff)

    return JsonResponse({'success': True, 'is_bookable': is_bookable})


# =============================================================================
# Schedules
# =============================================================================

@login_required
@module_view("staff", "schedules")
def schedule_list(request):
    """List all staff schedules."""
    staff_members = StaffMember.objects.filter(status='active').prefetch_related('schedules')

    return {
        'staff_members': staff_members,
    }


@login_required
def schedule_create(request, staff_pk):
    """Create a schedule for staff member."""
    staff = get_object_or_404(StaffMember, pk=staff_pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            schedule, error = StaffServiceLayer.create_schedule(
                staff=staff,
                name=data.get('name', 'New Schedule'),
                is_default=data.get('is_default', 'false') in ['true', True, '1', 1],
            )

            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True, 'id': schedule.id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'staff/schedule_form.html', {
        'mode': 'create',
        'staff': staff,
    })


@login_required
def schedule_detail(request, pk):
    """Schedule detail with working hours."""
    schedule = get_object_or_404(StaffSchedule, pk=pk)
    working_hours = schedule.working_hours.all()

    return render(request, 'staff/schedule_detail.html', {
        'schedule': schedule,
        'working_hours': working_hours,
    })


@login_required
def schedule_edit(request, pk):
    """Edit a schedule."""
    schedule = get_object_or_404(StaffSchedule, pk=pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            success, error = StaffServiceLayer.update_schedule(
                schedule,
                name=data.get('name', schedule.name),
                is_default=data.get('is_default', 'false') in ['true', True, '1', 1],
            )

            if not success:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'staff/schedule_form.html', {
        'mode': 'edit',
        'schedule': schedule,
        'staff': schedule.staff,
    })


@login_required
@require_POST
def schedule_delete(request, pk):
    """Delete a schedule."""
    schedule = get_object_or_404(StaffSchedule, pk=pk)
    success, error = StaffServiceLayer.delete_schedule(schedule)

    if not success:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True})


@login_required
@require_POST
def working_hours_save(request, schedule_pk):
    """Save working hours for a schedule."""
    schedule = get_object_or_404(StaffSchedule, pk=schedule_pk)

    try:
        data = json.loads(request.body)
        hours_data = data.get('hours', [])

        # Convert time strings to time objects
        for h in hours_data:
            if 'start_time' in h and isinstance(h['start_time'], str):
                h['start_time'] = datetime.strptime(h['start_time'], '%H:%M').time()
            if 'end_time' in h and isinstance(h['end_time'], str):
                h['end_time'] = datetime.strptime(h['end_time'], '%H:%M').time()
            if h.get('break_start') and isinstance(h['break_start'], str):
                h['break_start'] = datetime.strptime(h['break_start'], '%H:%M').time()
            if h.get('break_end') and isinstance(h['break_end'], str):
                h['break_end'] = datetime.strptime(h['break_end'], '%H:%M').time()

        success, error = StaffServiceLayer.save_working_hours(schedule, hours_data)

        if not success:
            return JsonResponse({'success': False, 'error': error}, status=400)

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# Time Off
# =============================================================================

@login_required
def time_off_list(request, staff_pk):
    """List time off for a staff member."""
    staff = get_object_or_404(StaffMember, pk=staff_pk)
    time_off = staff.time_off.order_by('-start_date')

    return render(request, 'staff/time_off_list.html', {
        'staff': staff,
        'time_off': time_off,
    })


@login_required
def time_off_create(request, staff_pk):
    """Create time off request."""
    staff = get_object_or_404(StaffMember, pk=staff_pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

            time_off, error = StaffServiceLayer.create_time_off(
                staff=staff,
                start_date=start_date,
                end_date=end_date,
                leave_type=data.get('leave_type', 'vacation'),
                reason=data.get('reason', ''),
                is_full_day=data.get('is_full_day', 'true') in ['true', True, '1', 1],
            )

            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True, 'id': time_off.id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'staff/time_off_form.html', {
        'mode': 'create',
        'staff': staff,
    })


@login_required
def time_off_edit(request, pk):
    """Edit time off request."""
    time_off = get_object_or_404(StaffTimeOff, pk=pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            kwargs = {}
            if 'start_date' in data:
                kwargs['start_date'] = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            if 'end_date' in data:
                kwargs['end_date'] = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            if 'leave_type' in data:
                kwargs['leave_type'] = data['leave_type']
            if 'reason' in data:
                kwargs['reason'] = data['reason']

            success, error = StaffServiceLayer.update_time_off(time_off, **kwargs)

            if not success:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'staff/time_off_form.html', {
        'mode': 'edit',
        'time_off': time_off,
        'staff': time_off.staff,
    })


@login_required
@require_POST
def time_off_delete(request, pk):
    """Delete time off request."""
    time_off = get_object_or_404(StaffTimeOff, pk=pk)
    success, error = StaffServiceLayer.delete_time_off(time_off)

    if not success:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True})


@login_required
@require_POST
def time_off_approve(request, pk):
    """Approve time off request."""
    time_off = get_object_or_404(StaffTimeOff, pk=pk)
    user_id = request.session.get('local_user_id', 1)
    success, error = StaffServiceLayer.approve_time_off(time_off, user_id)

    if not success:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True})


# =============================================================================
# Staff Services
# =============================================================================

@login_required
def staff_services(request, staff_pk):
    """Manage services for staff member."""
    staff = get_object_or_404(StaffMember, pk=staff_pk)
    services = staff.staff_services.all()

    return render(request, 'staff/staff_services.html', {
        'staff': staff,
        'services': services,
    })


@login_required
@require_POST
def staff_services_save(request, staff_pk):
    """Save staff services."""
    staff = get_object_or_404(StaffMember, pk=staff_pk)

    try:
        data = json.loads(request.body)
        service_data = data.get('services', [])

        success, error = StaffServiceLayer.assign_services(staff, service_data)

        if not success:
            return JsonResponse({'success': False, 'error': error}, status=400)

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# Roles
# =============================================================================

@login_required
def role_list(request):
    """List all roles."""
    roles = StaffRole.objects.all().order_by('order', 'name')

    return render(request, 'staff/role_list.html', {
        'roles': roles,
    })


@login_required
def role_create(request):
    """Create a role."""
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            role, error = StaffServiceLayer.create_role(
                name=data.get('name', ''),
                description=data.get('description', ''),
                color=data.get('color', ''),
                order=int(data.get('order', 0)),
            )

            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True, 'id': role.id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'staff/role_form.html', {
        'mode': 'create',
    })


@login_required
def role_edit(request, pk):
    """Edit a role."""
    role = get_object_or_404(StaffRole, pk=pk)

    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            kwargs = {}
            if 'name' in data:
                kwargs['name'] = data['name']
            if 'description' in data:
                kwargs['description'] = data['description']
            if 'color' in data:
                kwargs['color'] = data['color']
            if 'order' in data:
                kwargs['order'] = int(data['order'])
            if 'is_active' in data:
                kwargs['is_active'] = data['is_active'] in ['true', True, '1', 1]

            success, error = StaffServiceLayer.update_role(role, **kwargs)

            if not success:
                return JsonResponse({'success': False, 'error': error}, status=400)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'staff/role_form.html', {
        'mode': 'edit',
        'role': role,
    })


@login_required
@require_POST
def role_delete(request, pk):
    """Delete a role."""
    role = get_object_or_404(StaffRole, pk=pk)
    success, error = StaffServiceLayer.delete_role(role)

    if not success:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True})


# =============================================================================
# Settings
# =============================================================================

@login_required
@module_view("staff", "settings")
def settings_view(request):
    """Settings page."""
    config = StaffConfig.get_config()
    return {'config': config}


@login_required
@require_POST
def settings_save(request):
    """Save settings."""
    config = StaffConfig.get_config()

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        if 'default_work_start' in data:
            config.default_work_start = datetime.strptime(data['default_work_start'], '%H:%M').time()
        if 'default_work_end' in data:
            config.default_work_end = datetime.strptime(data['default_work_end'], '%H:%M').time()
        if 'default_break_duration' in data:
            config.default_break_duration = int(data['default_break_duration'])
        if 'min_advance_booking' in data:
            config.min_advance_booking = int(data['min_advance_booking'])
        if 'max_daily_hours' in data:
            config.max_daily_hours = int(data['max_daily_hours'])
        if 'overtime_threshold' in data:
            config.overtime_threshold = int(data['overtime_threshold'])

        config.save()
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def settings_toggle(request):
    """Toggle boolean settings."""
    config = StaffConfig.get_config()
    field = request.POST.get('field')

    toggleable_fields = [
        'show_staff_photos',
        'show_staff_bio',
        'allow_staff_selection',
        'notify_new_appointment',
        'notify_cancellation',
    ]

    if field not in toggleable_fields:
        return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)

    setattr(config, field, not getattr(config, field))
    config.save()

    return JsonResponse({'success': True, 'value': getattr(config, field)})


# =============================================================================
# API Endpoints
# =============================================================================

@login_required
@require_GET
def api_search(request):
    """Search staff API."""
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 20))

    staff_members = StaffServiceLayer.search_staff(
        query=query,
        status='active',
    )[:limit]

    results = [
        {
            'id': s.id,
            'name': s.full_name,
            'role': s.role.name if s.role else None,
            'is_bookable': s.is_bookable,
            'color': s.color,
        }
        for s in staff_members
    ]

    return JsonResponse({'results': results})


@login_required
@require_GET
def api_available(request):
    """Get available staff at datetime."""
    datetime_str = request.GET.get('datetime')
    service_id = request.GET.get('service_id')

    if not datetime_str:
        return JsonResponse({'error': 'datetime is required'}, status=400)

    try:
        target_dt = datetime.fromisoformat(datetime_str)
    except ValueError:
        return JsonResponse({'error': 'Invalid datetime format'}, status=400)

    available = StaffServiceLayer.get_available_staff(
        target_dt,
        service_id=int(service_id) if service_id else None,
    )

    results = [
        {
            'id': s.id,
            'name': s.full_name,
            'role': s.role.name if s.role else None,
            'color': s.color,
        }
        for s in available
    ]

    return JsonResponse({'available': results})


@login_required
@require_GET
def api_staff_schedule(request, pk):
    """Get staff schedule for a date."""
    staff = get_object_or_404(StaffMember, pk=pk)
    date_str = request.GET.get('date')

    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = date.today()

    duration = int(request.GET.get('duration', 60))
    interval = int(request.GET.get('interval', 15))

    slots = StaffServiceLayer.get_available_slots(
        staff,
        target_date,
        duration_minutes=duration,
        slot_interval=interval,
    )

    return JsonResponse({
        'staff_id': staff.id,
        'date': target_date.isoformat(),
        'slots': [s.strftime('%H:%M') for s in slots],
    })
