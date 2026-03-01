"""AI tools for the Staff module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListStaffMembers(AssistantTool):
    name = "list_staff_members"
    description = "List staff members with filters. Returns name, role, status, specialties, bookable status."
    module_id = "staff"
    required_permission = "staff.view_staffmember"
    parameters = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter: active, inactive, on_leave, terminated"},
            "role_id": {"type": "string", "description": "Filter by staff role ID"},
            "is_bookable": {"type": "boolean", "description": "Filter by bookable status"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from staff.models import StaffMember
        qs = StaffMember.objects.select_related('role').all()
        if args.get('status'):
            qs = qs.filter(status=args['status'])
        if args.get('role_id'):
            qs = qs.filter(role_id=args['role_id'])
        if 'is_bookable' in args:
            qs = qs.filter(is_bookable=args['is_bookable'])
        return {
            "staff": [
                {
                    "id": str(s.id), "first_name": s.first_name, "last_name": s.last_name,
                    "email": s.email, "phone": s.phone, "status": s.status,
                    "role": s.role.name if s.role else None,
                    "specialties": s.specialties, "is_bookable": s.is_bookable,
                    "hourly_rate": str(s.hourly_rate) if s.hourly_rate else None,
                    "commission_rate": str(s.commission_rate) if s.commission_rate else None,
                }
                for s in qs.order_by('order', 'first_name')
            ]
        }


@register_tool
class CreateStaffMember(AssistantTool):
    name = "create_staff_member"
    description = "Create a new staff member."
    module_id = "staff"
    required_permission = "staff.add_staffmember"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "first_name": {"type": "string"}, "last_name": {"type": "string"},
            "email": {"type": "string"}, "phone": {"type": "string"},
            "role_id": {"type": "string", "description": "Staff role ID"},
            "specialties": {"type": "string", "description": "Specialties/skills"},
            "is_bookable": {"type": "boolean", "description": "Can be booked for appointments"},
            "hourly_rate": {"type": "string", "description": "Hourly rate"},
            "commission_rate": {"type": "string", "description": "Commission percentage"},
            "bio": {"type": "string"},
            "color": {"type": "string", "description": "Calendar color"},
        },
        "required": ["first_name", "last_name"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from staff.models import StaffMember
        s = StaffMember.objects.create(
            first_name=args['first_name'], last_name=args['last_name'],
            email=args.get('email', ''), phone=args.get('phone', ''),
            role_id=args.get('role_id'),
            specialties=args.get('specialties', ''),
            is_bookable=args.get('is_bookable', False),
            hourly_rate=Decimal(args['hourly_rate']) if args.get('hourly_rate') else None,
            commission_rate=Decimal(args['commission_rate']) if args.get('commission_rate') else None,
            bio=args.get('bio', ''), color=args.get('color', ''),
        )
        return {"id": str(s.id), "name": f"{s.first_name} {s.last_name}", "created": True}


@register_tool
class ListStaffRoles(AssistantTool):
    name = "list_staff_roles"
    description = "List staff roles (e.g., 'Estilista Senior', 'Ayudante')."
    module_id = "staff"
    required_permission = "staff.view_staffrole"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from staff.models import StaffRole
        return {
            "roles": [
                {"id": str(r.id), "name": r.name, "color": r.color, "is_active": r.is_active}
                for r in StaffRole.objects.filter(is_active=True).order_by('order')
            ]
        }


@register_tool
class CreateStaffRole(AssistantTool):
    name = "create_staff_role"
    description = "Create a staff role (e.g., 'Estilista', 'Cocinero', 'Recepcionista')."
    module_id = "staff"
    required_permission = "staff.add_staffrole"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string"}, "description": {"type": "string"},
            "color": {"type": "string", "description": "Hex color"},
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from staff.models import StaffRole
        r = StaffRole.objects.create(
            name=args['name'], description=args.get('description', ''), color=args.get('color', ''),
        )
        return {"id": str(r.id), "name": r.name, "created": True}


@register_tool
class ListStaffTimeOff(AssistantTool):
    name = "list_staff_time_off"
    description = "List staff time off requests."
    module_id = "staff"
    required_permission = "staff.view_stafftimeoff"
    parameters = {
        "type": "object",
        "properties": {
            "staff_id": {"type": "string"}, "status": {"type": "string", "description": "pending, approved, rejected, cancelled"},
            "limit": {"type": "integer"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from staff.models import StaffTimeOff
        qs = StaffTimeOff.objects.select_related('staff_member').all()
        if args.get('staff_id'):
            qs = qs.filter(staff_member_id=args['staff_id'])
        if args.get('status'):
            qs = qs.filter(status=args['status'])
        limit = args.get('limit', 20)
        return {
            "time_off": [
                {
                    "id": str(t.id), "staff": f"{t.staff_member.first_name} {t.staff_member.last_name}",
                    "leave_type": t.leave_type, "start_date": str(t.start_date), "end_date": str(t.end_date),
                    "reason": t.reason, "status": t.status,
                }
                for t in qs.order_by('-start_date')[:limit]
            ]
        }


@register_tool
class CreateTimeOffRequest(AssistantTool):
    name = "create_time_off_request"
    description = "Create a time off request for a staff member."
    module_id = "staff"
    required_permission = "staff.add_stafftimeoff"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "staff_id": {"type": "string"}, "leave_type": {"type": "string", "description": "vacation, sick, personal, training, other"},
            "start_date": {"type": "string"}, "end_date": {"type": "string"},
            "reason": {"type": "string"}, "is_full_day": {"type": "boolean"},
        },
        "required": ["staff_id", "leave_type", "start_date", "end_date"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from staff.models import StaffTimeOff
        t = StaffTimeOff.objects.create(
            staff_member_id=args['staff_id'], leave_type=args['leave_type'],
            start_date=args['start_date'], end_date=args['end_date'],
            reason=args.get('reason', ''), is_full_day=args.get('is_full_day', True),
        )
        return {"id": str(t.id), "created": True}


@register_tool
class AssignServiceToStaff(AssistantTool):
    name = "assign_service_to_staff"
    description = "Assign a service to a staff member (for appointments/bookings)."
    module_id = "staff"
    required_permission = "staff.change_staffmember"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "staff_id": {"type": "string"}, "service_id": {"type": "string"},
            "custom_duration": {"type": "integer", "description": "Custom duration in minutes"},
            "custom_price": {"type": "string", "description": "Custom price"},
            "is_primary": {"type": "boolean", "description": "Is this their primary service"},
        },
        "required": ["staff_id", "service_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from staff.models import StaffService
        from services.models import Service
        service = Service.objects.get(id=args['service_id'])
        ss, created = StaffService.objects.update_or_create(
            staff_member_id=args['staff_id'], service=service,
            defaults={
                'service_name': service.name,
                'custom_duration': args.get('custom_duration'),
                'custom_price': Decimal(args['custom_price']) if args.get('custom_price') else None,
                'is_primary': args.get('is_primary', False),
            },
        )
        return {"id": str(ss.id), "service": service.name, "created": created}


@register_tool
class GetStaffSettings(AssistantTool):
    name = "get_staff_settings"
    description = "Get staff module settings."
    module_id = "staff"
    required_permission = "staff.view_staffmember"
    parameters = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

    def execute(self, args, request):
        from staff.models import StaffSettings
        s = StaffSettings.get_solo()
        return {
            "show_staff_photos": s.show_staff_photos,
            "allow_staff_selection": s.allow_staff_selection,
            "notify_new_appointment": s.notify_new_appointment,
            "overtime_threshold": s.overtime_threshold,
        }
