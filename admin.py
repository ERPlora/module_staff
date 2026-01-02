from django.contrib import admin
from .models import (
    StaffConfig,
    StaffRole,
    StaffMember,
    StaffSchedule,
    StaffWorkingHours,
    StaffTimeOff,
    StaffService,
)


@admin.register(StaffConfig)
class StaffConfigAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'default_work_start', 'default_work_end', 'updated_at']


@admin.register(StaffRole)
class StaffRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']


class StaffWorkingHoursInline(admin.TabularInline):
    model = StaffWorkingHours
    extra = 0


class StaffScheduleInline(admin.TabularInline):
    model = StaffSchedule
    extra = 0


class StaffServiceInline(admin.TabularInline):
    model = StaffService
    extra = 0


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'role', 'status', 'is_bookable', 'phone', 'email']
    list_filter = ['status', 'is_bookable', 'role']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'employee_id']
    inlines = [StaffScheduleInline, StaffServiceInline]


@admin.register(StaffSchedule)
class StaffScheduleAdmin(admin.ModelAdmin):
    list_display = ['staff', 'name', 'is_default', 'is_active']
    list_filter = ['is_active', 'is_default']
    search_fields = ['staff__first_name', 'staff__last_name', 'name']
    inlines = [StaffWorkingHoursInline]


@admin.register(StaffTimeOff)
class StaffTimeOffAdmin(admin.ModelAdmin):
    list_display = ['staff', 'leave_type', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'leave_type']
    search_fields = ['staff__first_name', 'staff__last_name', 'reason']
    date_hierarchy = 'start_date'
