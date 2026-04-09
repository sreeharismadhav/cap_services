from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum
from .models import StaffTask, ServiceBooking, StaffTracking, StaffShift, StaffPerformance, StaffDepartment, Department
from orders.models import Order
from accounts.models import User, Profile
from core.decorators import staff_required
from core.utils import log_activity
from .forms import ServiceBookingForm, StaffTaskForm, StaffShiftForm
import json
from core.views import get_base_template


@staff_required
def dashboard_redirect(request):
    """Redirect to appropriate department dashboard"""
    user = User.objects.get(id=request.session['user_id'])
    
    staff_depts = StaffDepartment.objects.filter(staff=user).select_related('department')
    
    if staff_depts.count() == 0:
        messages.warning(request, 'No department assigned. Please contact admin.')
        return redirect('staff:no_department')
    elif staff_depts.count() == 1:
        dept = staff_depts.first().department
        return redirect('staff:department_dashboard', dept_slug=dept.slug)
    else:
        return redirect('staff:select_department')


@staff_required
def select_department(request):
    """Show department selection for staff with multiple departments"""
    user = User.objects.get(id=request.session['user_id'])
    
    staff_depts = StaffDepartment.objects.filter(staff=user).select_related('department')
    departments = [sd.department for sd in staff_depts]
    
    context = {
        'departments': departments,
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'staff/select_department.html', context)


@staff_required
def no_department(request):
    """Page for staff with no department assigned"""
    context = {
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'staff/no_department.html', context)


@staff_required
def department_dashboard(request, dept_slug):
    """Department-specific dashboard"""
    user = User.objects.get(id=request.session['user_id'])
    department = get_object_or_404(Department, slug=dept_slug, is_active=True)
    
    if not StaffDepartment.objects.filter(staff=user, department=department).exists():
        messages.error(request, 'You are not authorized for this department')
        return redirect('staff:select_department')
    
    today = timezone.now().date()
    
    if department.slug == 'service-repair':
        pending_tasks = ServiceBooking.objects.filter(
            assigned_staff=user,
            status__in=['REQUESTED', 'ASSIGNED', 'IN_PROGRESS']
        ).order_by('-created_at')
        task_type_name = 'Service Requests'
        
        stats = {
            'pending': pending_tasks.count(),
            'completed_today': ServiceBooking.objects.filter(
                assigned_staff=user,
                status='COMPLETED',
                completed_at__date=today
            ).count(),
            'total_this_week': ServiceBooking.objects.filter(
                assigned_staff=user,
                created_at__week=today.isocalendar()[1]
            ).count(),
            'avg_rating': 0
        }
        
    elif department.slug == 'technical-support':
        pending_tasks = ServiceBooking.objects.filter(
            assigned_staff=user,
            status__in=['REQUESTED', 'ASSIGNED', 'IN_PROGRESS']
        ).order_by('-created_at')
        task_type_name = 'Support Tickets'
        
        stats = {
            'pending': pending_tasks.count(),
            'completed_today': ServiceBooking.objects.filter(
                assigned_staff=user,
                status='COMPLETED',
                completed_at__date=today
            ).count(),
            'total_this_week': ServiceBooking.objects.filter(
                assigned_staff=user,
                created_at__week=today.isocalendar()[1]
            ).count(),
            'avg_rating': 0
        }
        
    elif department.slug == 'courier':
        pending_tasks = StaffTask.objects.filter(
            staff=user,
            task_type='DELIVERY',
            status__in=['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS']
        ).order_by('-priority', 'assigned_at')
        task_type_name = 'Delivery Tasks'
        
        stats = {
            'pending': pending_tasks.count(),
            'completed_today': StaffTask.objects.filter(
                staff=user,
                task_type='DELIVERY',
                status='COMPLETED',
                completed_at__date=today
            ).count(),
            'total_this_week': StaffTask.objects.filter(
                staff=user,
                task_type='DELIVERY',
                created_at__week=today.isocalendar()[1]
            ).count(),
            'avg_rating': StaffTask.objects.filter(
                staff=user,
                customer_rating__isnull=False
            ).aggregate(Avg('customer_rating'))['customer_rating__avg'] or 0
        }
        
    elif department.slug == 'accounts':
        pending_tasks = StaffTask.objects.filter(
            staff=user,
            task_type='ACCOUNTS',
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).order_by('-assigned_at')
        task_type_name = 'Accounting Tasks'
        
        stats = {
            'pending': pending_tasks.count(),
            'completed_today': StaffTask.objects.filter(
                staff=user,
                task_type='ACCOUNTS',
                status='COMPLETED',
                completed_at__date=today
            ).count(),
            'total_this_week': StaffTask.objects.filter(
                staff=user,
                task_type='ACCOUNTS',
                created_at__week=today.isocalendar()[1]
            ).count(),
            'avg_rating': 0
        }
        
    elif department.slug == 'customer-support':
        pending_tasks = ServiceBooking.objects.filter(
            assigned_staff=user,
            status__in=['REQUESTED', 'ASSIGNED']
        ).order_by('-created_at')
        task_type_name = 'Support Tickets'
        
        stats = {
            'pending': pending_tasks.count(),
            'completed_today': ServiceBooking.objects.filter(
                assigned_staff=user,
                status='COMPLETED',
                completed_at__date=today
            ).count(),
            'total_this_week': ServiceBooking.objects.filter(
                assigned_staff=user,
                created_at__week=today.isocalendar()[1]
            ).count(),
            'avg_rating': 0
        }
        
    elif department.slug == 'quality-control':
        pending_tasks = StaffTask.objects.filter(
            staff=user,
            task_type='QUALITY',
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).order_by('-assigned_at')
        task_type_name = 'Quality Checks'
        
        stats = {
            'pending': pending_tasks.count(),
            'completed_today': StaffTask.objects.filter(
                staff=user,
                task_type='QUALITY',
                status='COMPLETED',
                completed_at__date=today
            ).count(),
            'total_this_week': StaffTask.objects.filter(
                staff=user,
                task_type='QUALITY',
                created_at__week=today.isocalendar()[1]
            ).count(),
            'avg_rating': 0
        }
        
    elif department.slug == 'inventory':
        pending_tasks = StaffTask.objects.filter(
            staff=user,
            task_type='INVENTORY',
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).order_by('-assigned_at')
        task_type_name = 'Inventory Tasks'
        
        stats = {
            'pending': pending_tasks.count(),
            'completed_today': StaffTask.objects.filter(
                staff=user,
                task_type='INVENTORY',
                status='COMPLETED',
                completed_at__date=today
            ).count(),
            'total_this_week': StaffTask.objects.filter(
                staff=user,
                task_type='INVENTORY',
                created_at__week=today.isocalendar()[1]
            ).count(),
            'avg_rating': 0
        }
        
    else:
        pending_tasks = StaffTask.objects.filter(
            staff=user,
            status__in=['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS']
        ).order_by('-priority', 'assigned_at')
        task_type_name = 'Tasks'
        
        stats = {
            'pending': pending_tasks.count(),
            'completed_today': StaffTask.objects.filter(
                staff=user,
                status='COMPLETED',
                completed_at__date=today
            ).count(),
            'total_this_week': StaffTask.objects.filter(
                staff=user,
                created_at__week=today.isocalendar()[1]
            ).count(),
            'avg_rating': StaffTask.objects.filter(
                staff=user,
                customer_rating__isnull=False
            ).aggregate(Avg('customer_rating'))['customer_rating__avg'] or 0
        }
    
    today_shift = StaffShift.objects.filter(staff=user, shift_date=today).first()
    
    context = {
        'user': user,
        'department': department,
        'pending_tasks': pending_tasks[:10],
        'stats': stats,
        'task_type_name': task_type_name,
        'today_shift': today_shift,
        'theme_color': department.color,
        'theme_light': f"{department.color}20",
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'staff/department_dashboard.html', context)


@staff_required
def dashboard(request):
    """Original dashboard - redirects to department selection"""
    return dashboard_redirect(request)


@staff_required
def task_list(request):
    """List all tasks for staff"""
    user = User.objects.get(id=request.session['user_id'])
    
    status_filter = request.GET.get('status', 'pending')
    
    if status_filter == 'pending':
        tasks = StaffTask.objects.filter(
            staff=user,
            status__in=['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS']
        )
    elif status_filter == 'completed':
        tasks = StaffTask.objects.filter(staff=user, status='COMPLETED')
    elif status_filter == 'all':
        tasks = StaffTask.objects.filter(staff=user)
    else:
        tasks = StaffTask.objects.filter(staff=user, status=status_filter)
    
    tasks = tasks.order_by('-priority', '-assigned_at')
    
    context = {
        'tasks': tasks,
        'current_filter': status_filter,
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'staff/task_list.html', context)


@staff_required
def task_detail(request, task_id):
    """Task details"""
    user = User.objects.get(id=request.session['user_id'])
    task = get_object_or_404(StaffTask, id=task_id, staff=user)
    
    context = {'task': task, 'base_template': get_base_template(request.session.get('user_role'))}
    return render(request, 'staff/task_detail.html', context)


@require_POST
@staff_required
def task_accept(request, task_id):
    """Accept a task"""
    user = User.objects.get(id=request.session['user_id'])
    task = get_object_or_404(StaffTask, id=task_id, staff=user)
    
    task.accept()
    log_activity(user, f'TASK_ACCEPTED_{task.id}', request=request)
    messages.success(request, 'Task accepted')
    return redirect('staff:task_detail', task_id=task.id)


@require_POST
@staff_required
def task_start(request, task_id):
    """Start a task"""
    user = User.objects.get(id=request.session['user_id'])
    task = get_object_or_404(StaffTask, id=task_id, staff=user)
    
    task.start()
    log_activity(user, f'TASK_STARTED_{task.id}', request=request)
    messages.success(request, 'Task started')
    return redirect('staff:task_detail', task_id=task.id)


@require_POST
@staff_required
def task_complete(request, task_id):
    """Complete a task"""
    user = User.objects.get(id=request.session['user_id'])
    task = get_object_or_404(StaffTask, id=task_id, staff=user)
    
    notes = request.POST.get('notes', '')
    task.complete(notes)
    
    performance, created = StaffPerformance.objects.get_or_create(
        staff=user,
        period_start=timezone.now().replace(day=1),
        period_end=timezone.now().replace(day=28)
    )
    performance.tasks_completed += 1
    performance.save()
    
    log_activity(user, f'TASK_COMPLETED_{task.id}', request=request)
    messages.success(request, 'Task completed')
    return redirect('staff:task_list')


@staff_required
def services_list(request):
    """List service bookings assigned to staff"""
    user = User.objects.get(id=request.session['user_id'])
    services = ServiceBooking.objects.filter(assigned_staff=user).order_by('-created_at')
    context = {'services': services, 'base_template': get_base_template(request.session.get('user_role'))}
    return render(request, 'staff/services_list.html', context)


@staff_required
def service_detail(request, service_id):
    """Service booking details"""
    user = User.objects.get(id=request.session['user_id'])
    service = get_object_or_404(ServiceBooking, id=service_id, assigned_staff=user)
    context = {'service': service, 'base_template': get_base_template(request.session.get('user_role'))}
    return render(request, 'staff/service_detail.html', context)


@require_POST
@staff_required
def service_update_status(request, service_id):
    """Update service status"""
    user = User.objects.get(id=request.session['user_id'])
    service = get_object_or_404(ServiceBooking, id=service_id, assigned_staff=user)
    
    new_status = request.POST.get('status')
    notes = request.POST.get('notes', '')
    
    if new_status:
        service.update_status(new_status, user, notes)
        messages.success(request, f'Service status updated to {new_status}')
    
    return redirect('staff:service_detail', service_id=service.id)


@require_POST
@staff_required
def update_location(request):
    """Update staff location"""
    user = User.objects.get(id=request.session['user_id'])
    data = json.loads(request.body)
    
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if latitude and longitude:
        StaffTracking.objects.create(staff=user, latitude=latitude, longitude=longitude)
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)


@staff_required
def shift_view(request):
    """View staff shift"""
    user = User.objects.get(id=request.session['user_id'])
    today = timezone.now().date()
    shift = StaffShift.objects.filter(staff=user, shift_date=today).first()
    context = {'shift': shift, 'base_template': get_base_template(request.session.get('user_role'))}
    return render(request, 'staff/shift.html', context)


@require_POST
@staff_required
def clock_in(request):
    """Clock in for shift"""
    user = User.objects.get(id=request.session['user_id'])
    today = timezone.now().date()
    shift = StaffShift.objects.filter(staff=user, shift_date=today).first()
    
    if shift:
        shift.clock_in_now()
        messages.success(request, f'Clocked in at {timezone.now().strftime("%H:%M")}')
    else:
        messages.error(request, 'No shift scheduled for today')
    
    return redirect('staff:shift')


@require_POST
@staff_required
def clock_out(request):
    """Clock out from shift"""
    user = User.objects.get(id=request.session['user_id'])
    today = timezone.now().date()
    shift = StaffShift.objects.filter(staff=user, shift_date=today, clock_in__isnull=False, clock_out__isnull=True).first()
    
    if shift:
        shift.clock_out_now()
        messages.success(request, f'Clocked out at {timezone.now().strftime("%H:%M")}')
    else:
        messages.error(request, 'No active shift found')
    
    return redirect('staff:shift')


@staff_required
def performance_view(request):
    """Staff performance metrics"""
    user = User.objects.get(id=request.session['user_id'])
    performances = StaffPerformance.objects.filter(staff=user).order_by('-period_start')[:12]
    context = {'performances': performances, 'base_template': get_base_template(request.session.get('user_role'))}
    return render(request, 'staff/performance.html', context)


@staff_required
def register_service_request(request):
    """Register walk-in/phone service request or complaint"""
    
    # Get the staff user and their department
    staff_user = User.objects.get(id=request.session['user_id'])
    staff_dept = StaffDepartment.objects.filter(staff=staff_user, is_primary=True).first()
    department = staff_dept.department if staff_dept else None
    
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        customer_email = request.POST.get('customer_email')
        customer_phone = request.POST.get('customer_phone')
        
        customer, created = User.objects.get_or_create(
            email=customer_email,
            defaults={
                'phone': customer_phone,
                'first_name': customer_name.split()[0] if customer_name else '',
                'last_name': ' '.join(customer_name.split()[1:]) if len(customer_name.split()) > 1 else '',
                'role': 'CUSTOMER',
                'is_active': True
            }
        )
        
        if created:
            Profile.objects.create(user=customer)
        
        request_type = request.POST.get('request_type')
        
        if request_type == 'complaint':
            device_type = 'Complaint'
            device_model = ''
            issue_description = f"Subject: {request.POST.get('subject')}\n\n{request.POST.get('description')}"
        else:
            device_type = request.POST.get('device_type')
            device_model = request.POST.get('device_model', '')
            issue_description = request.POST.get('issue_description')
        
        service = ServiceBooking.objects.create(
            user=customer,
            device_type=device_type,
            device_model=device_model,
            issue_description=issue_description,
            address_line1=request.POST.get('address_line1', ''),
            city=request.POST.get('city', ''),
            state=request.POST.get('state', ''),
            pincode=request.POST.get('pincode', ''),
            preferred_date=request.POST.get('preferred_date') or timezone.now().date(),
            preferred_time_slot=request.POST.get('preferred_time_slot', ''),
            status='REQUESTED',
            notes=request.POST.get('notes', ''),
            assigned_staff=staff_user
        )
        
        messages.success(request, f'Request #{service.booking_number} registered successfully')
        return redirect('staff:service_detail', service_id=service.id)
    
    context = {
        'department': department,  # ADD THIS LINE
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'staff/register_service_request.html', context)