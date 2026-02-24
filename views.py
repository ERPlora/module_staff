"""Staff module views."""

import json
from datetime import datetime, date, time, timedelta

from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.utils.translation import gettext_lazy as _

from apps.accounts.decorators import login_required
from apps.core.htmx import htmx_view
from apps.modules_runtime.navigation import with_module_nav

from .models import (
    StaffSettings,
    StaffRole,
    StaffMember,
    StaffSchedule,
    StaffWorkingHours,
    StaffTimeOff,
    StaffService,
)
from .forms import (
    StaffMemberForm,
    StaffRoleForm,
    StaffScheduleForm,
    StaffTimeOffForm,
    StaffSettingsForm,
)


def _hub(request):
    return request.session.get('hub_id')


def _employee(request):
    from apps.accounts.models import LocalUser
    uid = request.session.get('local_user_id')
    if uid:
        try:
            return LocalUser.objects.get(pk=uid)
        except LocalUser.DoesNotExist:
            pass
    return None


# =============================================================================
# Dashboard
# =============================================================================

@login_required
@with_module_nav('staff', 'dashboard')
@htmx_view('staff/pages/index.html', 'staff/partials/dashboard.html')
def index(request):
    return _dashboard_context(request)


@login_required
@with_module_nav('staff', 'dashboard')
@htmx_view('staff/pages/index.html', 'staff/partials/dashboard.html')
def dashboard(request):
    return _dashboard_context(request)


def _dashboard_context(request):
    hub = _hub(request)
    members = StaffMember.objects.filter(hub_id=hub, is_deleted=False)

    stats = {
        'total': members.count(),
        'active': members.filter(status='active').count(),
        'bookable': members.filter(status='active', is_bookable=True).count(),
        'on_leave': members.filter(status='on_leave').count(),
        'roles': StaffRole.objects.filter(hub_id=hub, is_deleted=False, is_active=True).count(),
    }

    recent_staff = members.filter(status='active').order_by('-created_at')[:5]
    pending_time_off = StaffTimeOff.objects.filter(
        hub_id=hub, is_deleted=False, status='pending'
    ).select_related('staff').order_by('start_date')[:5]

    return {
        'stats': stats,
        'recent_staff': recent_staff,
        'pending_time_off': pending_time_off,
    }


# =============================================================================
# Staff CRUD
# =============================================================================

@login_required
@with_module_nav('staff', 'list')
@htmx_view('staff/pages/list.html', 'staff/partials/list.html')
def staff_list(request):
    hub = _hub(request)
    search = request.GET.get('q', '')
    role_id = request.GET.get('role', '')
    status = request.GET.get('status', 'active')

    members = StaffMember.objects.filter(
        hub_id=hub, is_deleted=False
    ).select_related('role')

    if search:
        members = members.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(employee_id__icontains=search)
        )

    if status and status != 'all':
        members = members.filter(status=status)

    if role_id:
        members = members.filter(role_id=role_id)

    roles = StaffRole.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True
    ).order_by('order', 'name')

    return {
        'staff_members': members,
        'roles': roles,
        'search': search,
        'selected_role': role_id,
        'selected_status': status,
    }


@login_required
@with_module_nav('staff', 'list')
@htmx_view('staff/pages/create.html', 'staff/partials/form.html')
def staff_create(request):
    hub = _hub(request)

    if request.method == 'POST':
        form = StaffMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.hub_id = hub
            member.save()
            return JsonResponse({'success': True, 'id': str(member.pk)})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = StaffMemberForm()
    form.fields['role'].queryset = StaffRole.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True
    )

    return {'form': form, 'mode': 'create'}


@login_required
@with_module_nav('staff', 'list')
@htmx_view('staff/pages/detail.html', 'staff/partials/detail.html')
def staff_detail(request, pk):
    hub = _hub(request)
    member = StaffMember.objects.select_related('role', 'user').get(
        pk=pk, hub_id=hub, is_deleted=False
    )
    services = member.staff_services.filter(is_deleted=False, is_active=True)
    schedules = member.schedules.filter(is_deleted=False)
    recent_time_off = member.time_off.filter(is_deleted=False).order_by('-start_date')[:5]

    return {
        'staff': member,
        'services': services,
        'schedules': schedules,
        'recent_time_off': recent_time_off,
    }


@login_required
@with_module_nav('staff', 'list')
@htmx_view('staff/pages/edit.html', 'staff/partials/form.html')
def staff_edit(request, pk):
    hub = _hub(request)
    member = StaffMember.objects.get(pk=pk, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        form = StaffMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = StaffMemberForm(instance=member)
    form.fields['role'].queryset = StaffRole.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True
    )

    return {'form': form, 'staff': member, 'mode': 'edit'}


@login_required
@require_POST
def staff_delete(request, pk):
    hub = _hub(request)
    member = StaffMember.objects.get(pk=pk, hub_id=hub, is_deleted=False)
    member.is_deleted = True
    member.deleted_at = timezone.now()
    member.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def staff_toggle(request, pk):
    hub = _hub(request)
    member = StaffMember.objects.get(pk=pk, hub_id=hub, is_deleted=False)
    member.is_bookable = not member.is_bookable
    member.save(update_fields=['is_bookable', 'updated_at'])
    return JsonResponse({'success': True, 'is_bookable': member.is_bookable})


# =============================================================================
# Schedules
# =============================================================================

@login_required
@with_module_nav('staff', 'schedules')
@htmx_view('staff/pages/schedules.html', 'staff/partials/schedules.html')
def schedule_list(request):
    hub = _hub(request)
    members = StaffMember.objects.filter(
        hub_id=hub, is_deleted=False, status='active'
    ).prefetch_related('schedules')

    return {'staff_members': members}


@login_required
def schedule_create(request, staff_pk):
    hub = _hub(request)
    member = StaffMember.objects.get(pk=staff_pk, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        form = StaffScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.hub_id = hub
            schedule.staff = member
            schedule.save()
            return JsonResponse({'success': True, 'id': str(schedule.pk)})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = StaffScheduleForm()
    html = render_to_string('staff/partials/_schedule_form.html', {'form': form, 'staff': member}, request=request)
    return JsonResponse({'form_html': html})


@login_required
@with_module_nav('staff', 'schedules')
@htmx_view('staff/pages/schedule_detail.html', 'staff/partials/schedule_detail.html')
def schedule_detail(request, pk):
    hub = _hub(request)
    schedule = StaffSchedule.objects.select_related('staff').get(
        pk=pk, hub_id=hub, is_deleted=False
    )
    working_hours = schedule.working_hours.filter(is_deleted=False)

    return {
        'schedule': schedule,
        'working_hours': working_hours,
        'staff': schedule.staff,
    }


@login_required
def schedule_edit(request, pk):
    hub = _hub(request)
    schedule = StaffSchedule.objects.get(pk=pk, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        form = StaffScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = StaffScheduleForm(instance=schedule)
    html = render_to_string('staff/partials/_schedule_form.html', {'form': form, 'schedule': schedule, 'staff': schedule.staff}, request=request)
    return JsonResponse({'form_html': html})


@login_required
@require_POST
def schedule_delete(request, pk):
    hub = _hub(request)
    schedule = StaffSchedule.objects.get(pk=pk, hub_id=hub, is_deleted=False)
    schedule.is_deleted = True
    schedule.deleted_at = timezone.now()
    schedule.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def working_hours_save(request, schedule_pk):
    """Save working hours for a schedule (bulk)."""
    hub = _hub(request)
    schedule = StaffSchedule.objects.get(pk=schedule_pk, hub_id=hub, is_deleted=False)

    try:
        data = json.loads(request.body)
        hours_data = data.get('hours', [])

        # Delete existing and recreate
        schedule.working_hours.filter(is_deleted=False).delete()

        for h in hours_data:
            start_time = h.get('start_time')
            end_time = h.get('end_time')
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%H:%M').time()
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%H:%M').time()

            break_start = h.get('break_start')
            break_end = h.get('break_end')
            if break_start and isinstance(break_start, str):
                break_start = datetime.strptime(break_start, '%H:%M').time()
            if break_end and isinstance(break_end, str):
                break_end = datetime.strptime(break_end, '%H:%M').time()

            StaffWorkingHours.objects.create(
                hub_id=hub,
                schedule=schedule,
                day_of_week=int(h['day_of_week']),
                start_time=start_time,
                end_time=end_time,
                break_start=break_start or None,
                break_end=break_end or None,
                is_working=h.get('is_working', True),
            )

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# Time Off
# =============================================================================

@login_required
@with_module_nav('staff', 'list')
@htmx_view('staff/pages/time_off.html', 'staff/partials/time_off_list.html')
def time_off_list(request, staff_pk):
    hub = _hub(request)
    member = StaffMember.objects.get(pk=staff_pk, hub_id=hub, is_deleted=False)
    time_off = member.time_off.filter(is_deleted=False).order_by('-start_date')

    return {
        'staff': member,
        'time_off': time_off,
    }


@login_required
def time_off_create(request, staff_pk):
    hub = _hub(request)
    member = StaffMember.objects.get(pk=staff_pk, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        form = StaffTimeOffForm(request.POST)
        if form.is_valid():
            time_off = form.save(commit=False)
            time_off.hub_id = hub
            time_off.staff = member
            time_off.save()
            return JsonResponse({'success': True, 'id': str(time_off.pk)})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = StaffTimeOffForm()
    html = render_to_string('staff/partials/_time_off_form.html', {'form': form, 'staff': member}, request=request)
    return JsonResponse({'form_html': html})


@login_required
def time_off_edit(request, pk):
    hub = _hub(request)
    time_off = StaffTimeOff.objects.get(pk=pk, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        form = StaffTimeOffForm(request.POST, instance=time_off)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = StaffTimeOffForm(instance=time_off)
    html = render_to_string('staff/partials/_time_off_form.html', {'form': form, 'time_off': time_off, 'staff': time_off.staff}, request=request)
    return JsonResponse({'form_html': html})


@login_required
@require_POST
def time_off_delete(request, pk):
    hub = _hub(request)
    time_off = StaffTimeOff.objects.get(pk=pk, hub_id=hub, is_deleted=False)
    time_off.is_deleted = True
    time_off.deleted_at = timezone.now()
    time_off.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def time_off_approve(request, pk):
    hub = _hub(request)
    time_off = StaffTimeOff.objects.get(pk=pk, hub_id=hub, is_deleted=False)

    if time_off.status != 'pending':
        return JsonResponse(
            {'success': False, 'error': f'Cannot approve: status is {time_off.status}'},
            status=400
        )

    employee = _employee(request)
    time_off.status = 'approved'
    time_off.approved_by = employee
    time_off.approved_at = timezone.now()
    time_off.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def time_off_reject(request, pk):
    hub = _hub(request)
    time_off = StaffTimeOff.objects.get(pk=pk, hub_id=hub, is_deleted=False)

    if time_off.status != 'pending':
        return JsonResponse(
            {'success': False, 'error': f'Cannot reject: status is {time_off.status}'},
            status=400
        )

    time_off.status = 'rejected'
    time_off.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'success': True})


# =============================================================================
# Staff Services
# =============================================================================

@login_required
@with_module_nav('staff', 'list')
@htmx_view('staff/pages/staff_services.html', 'staff/partials/staff_services.html')
def staff_services(request, staff_pk):
    hub = _hub(request)
    member = StaffMember.objects.get(pk=staff_pk, hub_id=hub, is_deleted=False)
    services = member.staff_services.filter(is_deleted=False)

    return {
        'staff': member,
        'services': services,
    }


@login_required
@require_POST
def staff_services_save(request, staff_pk):
    """Save staff service assignments (bulk)."""
    hub = _hub(request)
    member = StaffMember.objects.get(pk=staff_pk, hub_id=hub, is_deleted=False)

    try:
        data = json.loads(request.body)
        service_data = data.get('services', [])

        # Remove existing assignments
        member.staff_services.filter(is_deleted=False).delete()

        for s in service_data:
            service_id = s.get('service_id')
            StaffService.objects.create(
                hub_id=hub,
                staff=member,
                service_id=service_id if service_id else None,
                service_name=s.get('service_name', ''),
                custom_duration=s.get('custom_duration') or None,
                custom_price=s.get('custom_price') or None,
                is_primary=s.get('is_primary', False),
                is_active=s.get('is_active', True),
            )

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# Roles
# =============================================================================

@login_required
@with_module_nav('staff', 'roles')
@htmx_view('staff/pages/roles.html', 'staff/partials/roles.html')
def role_list(request):
    hub = _hub(request)
    roles = StaffRole.objects.filter(
        hub_id=hub, is_deleted=False
    ).annotate(
        member_count=Count(
            'members',
            filter=Q(members__is_deleted=False)
        )
    ).order_by('order', 'name')

    return {'roles': roles}


@login_required
def role_add(request):
    hub = _hub(request)

    if request.method == 'POST':
        form = StaffRoleForm(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.hub_id = hub
            role.save()
            return JsonResponse({'success': True, 'id': str(role.pk)})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = StaffRoleForm()
    html = render_to_string('staff/partials/_role_form.html', {'form': form}, request=request)
    return JsonResponse({'form_html': html})


@login_required
def role_edit(request, pk):
    hub = _hub(request)
    role = StaffRole.objects.get(pk=pk, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        form = StaffRoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = StaffRoleForm(instance=role)
    html = render_to_string('staff/partials/_role_form.html', {'form': form, 'role': role}, request=request)
    return JsonResponse({'form_html': html})


@login_required
@require_POST
def role_delete(request, pk):
    hub = _hub(request)
    role = StaffRole.objects.get(pk=pk, hub_id=hub, is_deleted=False)

    # Unassign members from this role
    StaffMember.objects.filter(
        hub_id=hub, role=role, is_deleted=False
    ).update(role=None)

    role.is_deleted = True
    role.deleted_at = timezone.now()
    role.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


# =============================================================================
# Settings
# =============================================================================

@login_required
@with_module_nav('staff', 'settings')
@htmx_view('staff/pages/settings.html', 'staff/partials/settings.html')
def settings(request):
    hub = _hub(request)
    staff_settings = StaffSettings.get_settings(hub)
    form = StaffSettingsForm(instance=staff_settings)
    return {'settings': staff_settings, 'form': form}


@login_required
@require_POST
def settings_save(request):
    hub = _hub(request)
    staff_settings = StaffSettings.get_settings(hub)
    form = StaffSettingsForm(request.POST, instance=staff_settings)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@require_POST
def settings_toggle(request):
    hub = _hub(request)
    staff_settings = StaffSettings.get_settings(hub)
    field = request.POST.get('field', '')

    toggleable = [
        'show_staff_photos', 'show_staff_bio', 'allow_staff_selection',
        'notify_new_appointment', 'notify_cancellation',
    ]

    if field not in toggleable:
        return JsonResponse({'success': False, 'error': _('Invalid field')}, status=400)

    setattr(staff_settings, field, not getattr(staff_settings, field))
    staff_settings.save(update_fields=[field, 'updated_at'])
    return JsonResponse({'success': True, 'value': getattr(staff_settings, field)})


@login_required
@require_POST
def settings_input(request):
    hub = _hub(request)
    staff_settings = StaffSettings.get_settings(hub)
    field = request.POST.get('field', '')
    value = request.POST.get('value', '')

    input_fields = {
        'default_work_start': lambda v: datetime.strptime(v, '%H:%M').time(),
        'default_work_end': lambda v: datetime.strptime(v, '%H:%M').time(),
        'default_break_duration': int,
        'min_advance_booking': int,
        'max_daily_hours': int,
        'overtime_threshold': int,
    }

    if field not in input_fields:
        return JsonResponse({'success': False, 'error': _('Invalid field')}, status=400)

    try:
        parsed = input_fields[field](value)
        setattr(staff_settings, field, parsed)
        staff_settings.save(update_fields=[field, 'updated_at'])
        return JsonResponse({'success': True})
    except (ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def settings_reset(request):
    hub = _hub(request)
    staff_settings = StaffSettings.get_settings(hub)
    defaults = StaffSettings()
    for f in StaffSettingsForm.Meta.fields:
        setattr(staff_settings, f, getattr(defaults, f))
    staff_settings.save()
    return JsonResponse({'success': True})


# =============================================================================
# API Endpoints
# =============================================================================

@login_required
@require_GET
def api_search(request):
    hub = _hub(request)
    query = request.GET.get('q', '')
    limit = min(int(request.GET.get('limit', 20)), 50)

    if len(query) < 2:
        return JsonResponse({'results': []})

    members = StaffMember.objects.filter(
        hub_id=hub, is_deleted=False, status='active'
    ).filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).select_related('role')[:limit]

    results = [{
        'id': str(m.pk),
        'name': m.full_name,
        'role': m.role.name if m.role else None,
        'is_bookable': m.is_bookable,
        'color': m.color,
    } for m in members]

    return JsonResponse({'results': results})


@login_required
@require_GET
def api_available(request):
    """Get available staff at a specific datetime."""
    hub = _hub(request)
    datetime_str = request.GET.get('datetime')
    service_id = request.GET.get('service_id')

    if not datetime_str:
        return JsonResponse({'error': 'datetime is required'}, status=400)

    try:
        target_dt = datetime.fromisoformat(datetime_str)
    except ValueError:
        return JsonResponse({'error': 'Invalid datetime format'}, status=400)

    target_date = target_dt.date()
    target_time = target_dt.time()
    day_of_week = target_date.weekday()

    # Get active bookable staff
    members = StaffMember.objects.filter(
        hub_id=hub, is_deleted=False,
        status='active', is_bookable=True,
    ).select_related('role')

    # Filter by service if provided
    if service_id:
        members = members.filter(
            staff_services__service_id=service_id,
            staff_services__is_active=True,
            staff_services__is_deleted=False,
        )

    available = []
    for member in members:
        # Check time off
        has_time_off = member.time_off.filter(
            is_deleted=False,
            status__in=['pending', 'approved'],
            start_date__lte=target_date,
            end_date__gte=target_date,
        ).exists()
        if has_time_off:
            continue

        # Check working hours
        schedule = member.schedules.filter(
            is_deleted=False, is_active=True
        ).filter(
            Q(effective_from__isnull=True) | Q(effective_from__lte=target_date),
            Q(effective_until__isnull=True) | Q(effective_until__gte=target_date),
        ).order_by('-is_default').first()

        if schedule:
            hours = schedule.working_hours.filter(
                is_deleted=False, day_of_week=day_of_week, is_working=True
            ).first()
            if hours:
                if hours.start_time <= target_time <= hours.end_time:
                    # Check not during break
                    if hours.break_start and hours.break_end:
                        if hours.break_start <= target_time <= hours.break_end:
                            continue
                    available.append(member)

    results = [{
        'id': str(m.pk),
        'name': m.full_name,
        'role': m.role.name if m.role else None,
        'color': m.color,
    } for m in available]

    return JsonResponse({'available': results})


@login_required
@require_GET
def api_staff_schedule(request, pk):
    """Get available time slots for a staff member on a date."""
    hub = _hub(request)
    member = StaffMember.objects.get(pk=pk, hub_id=hub, is_deleted=False)
    date_str = request.GET.get('date')

    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = date.today()

    duration = int(request.GET.get('duration', 60))
    interval = int(request.GET.get('interval', 15))

    # Find applicable schedule
    schedule = member.schedules.filter(
        is_deleted=False, is_active=True
    ).filter(
        Q(effective_from__isnull=True) | Q(effective_from__lte=target_date),
        Q(effective_until__isnull=True) | Q(effective_until__gte=target_date),
    ).order_by('-is_default').first()

    slots = []
    if schedule:
        day_of_week = target_date.weekday()
        hours = schedule.working_hours.filter(
            is_deleted=False, day_of_week=day_of_week, is_working=True
        ).first()

        if hours:
            current = datetime.combine(target_date, hours.start_time)
            end = datetime.combine(target_date, hours.end_time)
            slot_duration = timedelta(minutes=duration)
            slot_interval = timedelta(minutes=interval)

            while current + slot_duration <= end:
                slot_time = current.time()

                # Skip break time
                if hours.break_start and hours.break_end:
                    slot_end_time = (current + slot_duration).time()
                    if not (slot_end_time <= hours.break_start or slot_time >= hours.break_end):
                        current += slot_interval
                        continue

                slots.append(slot_time.strftime('%H:%M'))
                current += slot_interval

    return JsonResponse({
        'staff_id': str(member.pk),
        'date': target_date.isoformat(),
        'slots': slots,
    })
