"""Staff URL Configuration."""

from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Dashboard
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Staff CRUD
    path('list/', views.staff_list, name='list'),
    path('create/', views.staff_create, name='create'),
    path('<uuid:pk>/', views.staff_detail, name='detail'),
    path('<uuid:pk>/edit/', views.staff_edit, name='edit'),
    path('<uuid:pk>/delete/', views.staff_delete, name='delete'),
    path('<uuid:pk>/toggle/', views.staff_toggle, name='toggle'),

    # Schedules
    path('schedules/', views.schedule_list, name='schedules'),
    path('<uuid:staff_pk>/schedule/create/', views.schedule_create, name='schedule_create'),
    path('schedule/<uuid:pk>/', views.schedule_detail, name='schedule_detail'),
    path('schedule/<uuid:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedule/<uuid:pk>/delete/', views.schedule_delete, name='schedule_delete'),

    # Working Hours
    path('schedule/<uuid:schedule_pk>/hours/save/', views.working_hours_save, name='working_hours_save'),

    # Time Off
    path('<uuid:staff_pk>/time-off/', views.time_off_list, name='time_off_list'),
    path('<uuid:staff_pk>/time-off/create/', views.time_off_create, name='time_off_create'),
    path('time-off/<uuid:pk>/edit/', views.time_off_edit, name='time_off_edit'),
    path('time-off/<uuid:pk>/delete/', views.time_off_delete, name='time_off_delete'),
    path('time-off/<uuid:pk>/approve/', views.time_off_approve, name='time_off_approve'),
    path('time-off/<uuid:pk>/reject/', views.time_off_reject, name='time_off_reject'),

    # Staff Services
    path('<uuid:staff_pk>/services/', views.staff_services, name='staff_services'),
    path('<uuid:staff_pk>/services/save/', views.staff_services_save, name='staff_services_save'),

    # Roles
    path('roles/', views.role_list, name='role_list'),
    path('roles/add/', views.role_add, name='role_add'),
    path('roles/<uuid:pk>/edit/', views.role_edit, name='role_edit'),
    path('roles/<uuid:pk>/delete/', views.role_delete, name='role_delete'),

    # Settings
    path('settings/', views.settings, name='settings'),
    path('settings/save/', views.settings_save, name='settings_save'),
    path('settings/toggle/', views.settings_toggle, name='settings_toggle'),
    path('settings/input/', views.settings_input, name='settings_input'),
    path('settings/reset/', views.settings_reset, name='settings_reset'),

    # API
    path('api/search/', views.api_search, name='api_search'),
    path('api/available/', views.api_available, name='api_available'),
    path('api/<uuid:pk>/schedule/', views.api_staff_schedule, name='api_staff_schedule'),
]
