from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Dashboard URLs
    path('', views.dashboard_redirect, name='dashboard_redirect'),
    path('select-department/', views.select_department, name='select_department'),
    path('no-department/', views.no_department, name='no_department'),
    path('dashboard/<slug:dept_slug>/', views.department_dashboard, name='department_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Task URLs
    path('tasks/', views.task_list, name='task_list'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/accept/', views.task_accept, name='task_accept'),
    path('task/<int:task_id>/start/', views.task_start, name='task_start'),
    path('task/<int:task_id>/complete/', views.task_complete, name='task_complete'),
    
    # Service URLs
    path('services/', views.services_list, name='services_list'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('service/<int:service_id>/update-status/', views.service_update_status, name='service_update_status'),
    path('register-service/', views.register_service_request, name='register_service_request'),
    
    # Location
    path('update-location/', views.update_location, name='update_location'),
    
    # Shift URLs
    path('shift/', views.shift_view, name='shift'),
    path('clock-in/', views.clock_in, name='clock_in'),
    path('clock-out/', views.clock_out, name='clock_out'),
    
    # Performance
    path('performance/', views.performance_view, name='performance'),
]