from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Staff List
    path('list/', views.staff_list, name='list'),
    path('create/', views.staff_create, name='create'),
    path('<int:pk>/', views.staff_detail, name='detail'),
    path('<int:pk>/edit/', views.staff_edit, name='edit'),
    path('<int:pk>/delete/', views.staff_delete, name='delete'),
    path('<int:pk>/toggle/', views.staff_toggle, name='toggle'),

    # Schedules
    path('schedules/', views.schedule_list, name='schedules'),
    path('<int:staff_pk>/schedule/create/', views.schedule_create, name='schedule_create'),
    path('schedule/<int:pk>/', views.schedule_detail, name='schedule_detail'),
    path('schedule/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedule/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),

    # Working Hours
    path('schedule/<int:schedule_pk>/hours/save/', views.working_hours_save, name='working_hours_save'),

    # Time Off
    path('<int:staff_pk>/time-off/', views.time_off_list, name='time_off_list'),
    path('<int:staff_pk>/time-off/create/', views.time_off_create, name='time_off_create'),
    path('time-off/<int:pk>/edit/', views.time_off_edit, name='time_off_edit'),
    path('time-off/<int:pk>/delete/', views.time_off_delete, name='time_off_delete'),
    path('time-off/<int:pk>/approve/', views.time_off_approve, name='time_off_approve'),

    # Staff Services
    path('<int:staff_pk>/services/', views.staff_services, name='staff_services'),
    path('<int:staff_pk>/services/save/', views.staff_services_save, name='staff_services_save'),

    # Roles
    path('roles/', views.role_list, name='role_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:pk>/edit/', views.role_edit, name='role_edit'),
    path('roles/<int:pk>/delete/', views.role_delete, name='role_delete'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/save/', views.settings_save, name='settings_save'),
    path('settings/toggle/', views.settings_toggle, name='settings_toggle'),

    # API endpoints
    path('api/search/', views.api_search, name='api_search'),
    path('api/available/', views.api_available, name='api_available'),
    path('api/<int:pk>/schedule/', views.api_staff_schedule, name='api_staff_schedule'),
]
