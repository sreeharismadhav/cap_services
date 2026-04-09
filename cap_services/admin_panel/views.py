from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncMonth
from jmespath import search
from core.decorators import admin_required
from core.utils import log_activity, generate_sku
from accounts.models import User, UserAddress
from store.models import Product, Category, Inventory, InventoryHistory, ProductImage
from orders.models import Order, OrderItem, Coupon, CouponUsage, CouponType
from staff.models import StaffTask, ServiceBooking, StaffPerformance, Department, StaffDepartment
from .models import AdminAlert, SystemReport, Announcement, ReportType
from .forms import AnnouncementForm
from core.views import get_base_template
import json
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.utils.text import slugify
import csv
from django.http import HttpResponse
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt

@admin_required
def dashboard(request):
    """Main admin dashboard"""
    user = User.objects.get(id=request.session['user_id'])
    
    # Get date range for today
    today = timezone.now().date()
    start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end_of_day = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    # Statistics
    stats = {
        'total_customers': User.objects.filter(role='CUSTOMER').count(),
        'total_staff': User.objects.filter(role='STAFF').count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status__in=['PLACED', 'CONFIRMED']).count(),
        'today_orders': Order.objects.filter(created_at__date=today).count(),
        'today_revenue': Order.objects.filter(
            created_at__date=today,
            payment_status='PAID'
        ).aggregate(total=Sum('total'))['total'] or 0,
        'total_revenue': Order.objects.filter(payment_status='PAID').aggregate(total=Sum('total'))['total'] or 0,
        'low_stock': Inventory.objects.filter(quantity__lte=F('low_stock_threshold')).count(),
        'pending_services': ServiceBooking.objects.filter(status='REQUESTED').count(),
    }
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Recent staff tasks
    recent_tasks = StaffTask.objects.select_related('staff').order_by('-assigned_at')[:10]
    
    context = {
        'user': user,
        'stats': stats,
        'recent_orders': recent_orders,
        'recent_tasks': recent_tasks,
    }
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def users_list(request):
    """List all users"""
    users_list = User.objects.all().order_by('-created_at')
    
    role_filter = request.GET.get('role')
    if role_filter:
        users = users_list.filter(role=role_filter)

    search = request.GET.get('search')
    if search:
        users = users_list.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search)
        )
    
    paginator = Paginator(users_list, 20)
    page = request.GET.get('page')
    users = paginator.get_page(page)

    context = {
        'users': users,
        'role_filter': role_filter,
        'search': search,
    }
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/users.html', context)


@admin_required
def user_detail(request, user_id):
    """View user details"""
    user_obj = get_object_or_404(User, id=user_id)
    addresses = UserAddress.objects.filter(user=user_obj)
    orders = Order.objects.filter(user=user_obj).order_by('-created_at')[:10]
    services = ServiceBooking.objects.filter(user=user_obj).order_by('-created_at')[:10]
    
    context = {
        'user_obj': user_obj,  # Change from 'user' to 'user_obj'
        'addresses': addresses,
        'orders': orders,
        'services': services,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/user_detail.html', context)


@admin_required
def staff_list(request):
    """List all staff members with department filter"""
    staff_members = User.objects.filter(role='STAFF').order_by('-created_at')
    
    # Department filter
    dept_slug = request.GET.get('dept')
    if dept_slug:
        department = get_object_or_404(Department, slug=dept_slug)
        staff_ids = StaffDepartment.objects.filter(department=department).values_list('staff_id', flat=True)
        staff_members = staff_members.filter(id__in=staff_ids)
    
    # Search
    if request.GET.get('search'):
        search = request.GET.get('search')
    else:
        search = ""
    if search:
        staff_members = staff_members.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Get department info for each staff
    staff_data = []
    for staff in staff_members:
        departments = StaffDepartment.objects.filter(staff=staff).select_related('department')
        staff_data.append({
            'staff': staff,
            'departments': departments,
            'primary_dept': departments.filter(is_primary=True).first(),
            'task_count': StaffTask.objects.filter(staff=staff, status__in=['ASSIGNED', 'IN_PROGRESS']).count()
        })
    
    departments = Department.objects.filter(is_active=True)
    
    context = {
        'staff': staff_data,
        'departments': departments,
        'selected_dept': dept_slug,
        'search': search,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/staff.html', context)

@admin_required
def staff_assign_departments(request, staff_id):
    staff = get_object_or_404(User, id=staff_id, role='STAFF')
    
    if request.method == 'POST':
        # Clear existing
        StaffDepartment.objects.filter(staff=staff).delete()
        
        # Get selected departments
        dept_ids = request.POST.getlist('departments')
        primary_id = request.POST.get('primary_department')
        
        for dept_id in dept_ids:
            StaffDepartment.objects.create(
                staff=staff,
                department_id=dept_id,
                is_primary=(dept_id == primary_id)
            )
        
        # FIXED - use first_name and last_name
        staff_name = f"{staff.first_name} {staff.last_name}".strip() or staff.email
        messages.success(request, f'Departments assigned to {staff_name}')
        return redirect('admin_panel:staff_detail', staff_id=staff.id)
    
    context = {
        'staff': staff,
        'departments': Department.objects.filter(is_active=True),
        'assigned_depts': list(StaffDepartment.objects.filter(staff=staff).values_list('department_id', flat=True)),
        'primary_dept_id': StaffDepartment.objects.filter(staff=staff, is_primary=True).values_list('department_id', flat=True).first(),
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/staff_assign_departments.html', context)

@admin_required
def staff_add(request):
    """Add new staff member"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        role = request.POST.get('role', 'STAFF')
        password = request.POST.get('password')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('admin_panel:staff')
        
        # Create user
        user = User.objects.create(
            email=email,
            phone=phone,
            role=role,
            is_active=True
        )
        
        # Split name into first and last
        name_parts = name.strip().split(' ', 1)
        user.first_name = name_parts[0]
        if len(name_parts) > 1:
            user.last_name = name_parts[1]
        
        user.set_password(password)
        user.save()
        
        # Create profile
        from accounts.models import Profile
        Profile.objects.create(user=user)
        
        messages.success(request, f'Staff member {user.email} added successfully')
        # FIXED: Use staff_id instead of user_id
        return redirect('admin_panel:staff_detail', staff_id=user.id)
    
    return redirect('admin_panel:staff')


@admin_required
def staff_detail(request, staff_id):
    """View staff details and performance"""
    staff = get_object_or_404(User, id=staff_id, role='STAFF')
    
    tasks = StaffTask.objects.filter(staff=staff).order_by('-assigned_at')[:20]
    performance = StaffPerformance.objects.filter(staff=staff).order_by('-period_start')[:6]
    
    context = {
        'staff': staff,
        'tasks': tasks,
        'performance': performance,
    }
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/staff_detail.html', context)


# FIX 1: Removed duplicate @admin_required
@admin_required
def product_list(request):
    """List all products"""
    products = Product.objects.all().order_by('-created_at')
    
    # Search
    search = request.GET.get('search')
    if search:
        products = products.filter(name__icontains=search)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Pagination
    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'categories': categories,
        'search': search,
        'category_id': category_id,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/products.html', context)


@admin_required
def product_create(request):
    """Create new product"""
    categories = Category.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        discounted_price = request.POST.get('discounted_price')
        description = request.POST.get('description')
        status = request.POST.get('status', 'ACTIVE')
        is_featured = request.POST.get('is_featured') == 'on'
        stock = request.POST.get('stock', 0)
        
        # Validation
        if not name or not category_id or not price:
            messages.error(request, 'Please fill all required fields')
            return redirect('admin_panel:product_create')
        
        # Create product
        category = Category.objects.get(id=category_id)
        product = Product.objects.create(
            category=category,
            name=name,
            slug=slugify(name),
            sku=generate_sku(),
            price=price,
            discounted_price=discounted_price or None,
            description=description,
            status=status,
            is_featured=is_featured
        )
        
        # Create inventory
        Inventory.objects.create(
            product=product,
            quantity=int(stock),
            reserved=0
        )
        
        # Handle images
        images = request.FILES.getlist('images')
        for i, img in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=img,
                is_primary=(i == 0),
                order=i
            )
        
        messages.success(request, f'Product "{product.name}" created successfully')
        return redirect('admin_panel:product_edit', product_id=product.id)
    
    context = {
        'categories': categories,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/product_form.html', context)


@admin_required
def product_edit(request, product_id):
    """Edit product"""
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.filter(is_active=True)
    inventory = product.inventory if hasattr(product, 'inventory') else None
    product_images = product.images.all().order_by('order', '-is_primary')
    
    if request.method == 'POST':
        # Check if this is an AJAX image operation
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            action = request.POST.get('action')
            
            # Delete image
            if action == 'delete_image':
                image_id = request.POST.get('image_id')
                try:
                    image = ProductImage.objects.get(id=image_id, product=product)
                    image.image.delete(save=False)
                    image.delete()
                    return JsonResponse({'success': True, 'message': 'Image deleted successfully'})
                except ProductImage.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Image not found'}, status=404)
            
            # Set primary image
            elif action == 'set_primary':
                image_id = request.POST.get('image_id')
                try:
                    image = ProductImage.objects.get(id=image_id, product=product)
                    image.is_primary = True
                    image.save()
                    return JsonResponse({'success': True, 'message': 'Primary image updated'})
                except ProductImage.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Image not found'}, status=404)
            
            # Reorder images
            elif action == 'reorder':
                orders = request.POST.getlist('orders[]')
                for order_data in orders:
                    try:
                        image_id, position = order_data.split(':')
                        ProductImage.objects.filter(id=image_id, product=product).update(order=int(position))
                    except:
                        pass
                return JsonResponse({'success': True, 'message': 'Images reordered'})
        
        # Regular form submission (save all data)
        # Update basic info
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category')
        product.price = request.POST.get('price')
        product.discounted_price = request.POST.get('discounted_price') or None
        product.description = request.POST.get('description')
        product.status = request.POST.get('status', 'ACTIVE')
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.slug = slugify(product.name)
        product.save()
        
        # Handle main product image - Create ProductImage as primary
        if request.FILES.get('main_image'):
            # Delete existing primary images
            product.images.filter(is_primary=True).delete()
            # Create new primary image
            ProductImage.objects.create(
                product=product,
                image=request.FILES.get('main_image'),
                is_primary=True,
                order=0
            )
        
        # Handle additional images upload
        if request.FILES.getlist('additional_images'):
            existing_count = product_images.count()
            for index, img in enumerate(request.FILES.getlist('additional_images')):
                ProductImage.objects.create(
                    product=product,
                    image=img,
                    is_primary=False,
                    order=existing_count + index + 1
                )
        
        # Handle image deletions from form
        delete_images = request.POST.getlist('delete_images')
        if delete_images:
            for img_id in delete_images:
                try:
                    img = ProductImage.objects.get(id=img_id, product=product)
                    img.image.delete(save=False)
                    img.delete()
                except ProductImage.DoesNotExist:
                    pass
        
        # Handle primary image selection from form
        primary_image_id = request.POST.get('primary_image')
        if primary_image_id:
            try:
                # Reset all to non-primary
                product.images.all().update(is_primary=False)
                # Set selected as primary
                primary_img = ProductImage.objects.get(id=primary_image_id, product=product)
                primary_img.is_primary = True
                primary_img.save()
            except ProductImage.DoesNotExist:
                pass
        
        # Update inventory
        stock = request.POST.get('stock', 0)
        if inventory:
            inventory.quantity = int(stock)
            inventory.save()
        else:
            Inventory.objects.create(
                product=product,
                quantity=int(stock),
                reserved=0
            )
        
        messages.success(request, f'Product "{product.name}" updated successfully')
        return redirect('admin_panel:product_edit', product_id=product.id)
    
    context = {
        'product': product,
        'categories': categories,
        'inventory': inventory,
        'product_images': product_images,
        'primary_image': product_images.filter(is_primary=True).first(),
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/product_form.html', context)


@admin_required
def product_delete(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully')
        return redirect('admin_panel:products')
    
    context = {
        'product': product,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/product_confirm_delete.html', context)


@admin_required
def product_image_delete(request, image_id):
    """Delete product image"""
    image = get_object_or_404(ProductImage, id=image_id)
    product_id = image.product.id
    
    if request.method == 'POST':
        # Delete file from storage
        if image.image:
            default_storage.delete(image.image.path)
        image.delete()
        
        # Set new primary image if deleted was primary
        if image.is_primary:
            first_image = ProductImage.objects.filter(product_id=product_id).first()
            if first_image:
                first_image.is_primary = True
                first_image.save()
        
        messages.success(request, 'Image deleted successfully')
    
    return redirect('admin_panel:product_edit', product_id=product_id)


@admin_required
def orders_list(request):
    """List all orders"""
    orders = Order.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    payment_filter = request.GET.get('payment')
    if payment_filter:
        orders = orders.filter(payment_status=payment_filter)
    
    search = request.GET.get('search')
    if search:
        orders = orders.filter(order_number__icontains=search)
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'search': search,
    }
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/orders.html', context)


@admin_required
def order_detail(request, order_id):
    """View order details"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {'order': order}
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/order_detail.html', context)


@require_POST
@admin_required
def update_order_status(request, order_id):
    """Update order status"""
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    notes = request.POST.get('notes', '')
    
    if new_status:
        user = User.objects.get(id=request.session['user_id'])
        order.update_status(new_status, user, notes)
        log_activity(user, f'ADMIN_UPDATE_ORDER_STATUS_{order.order_number}', request=request)
        messages.success(request, f'Order status updated to {new_status}')
    
    return redirect('admin_panel:order_detail', order_id=order.id)


@admin_required
def services_list(request):
    """List all service bookings"""
    services = ServiceBooking.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        services = services.filter(status=status_filter)
    
    # FIX 2: Removed undefined 'search' variable
    context = {
        'services': services,
        'total_services': ServiceBooking.objects.count(),
        'pending_services': ServiceBooking.objects.filter(status='REQUESTED').count(),
        'in_progress_services': ServiceBooking.objects.filter(status='IN_PROGRESS').count(),
        'completed_services': ServiceBooking.objects.filter(status='COMPLETED').count(),
        'status_filter': status_filter,
    }
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/services.html', context)


def export_services(request):
    """Export services to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="services_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Booking #', 'Customer', 'Device Type', 'Device Model', 'Issue', 'Preferred Date', 'Status', 'Created At'])
    
    services = ServiceBooking.objects.all().order_by('-created_at')
    for service in services:
        writer.writerow([
            service.booking_number,
            service.user.full_name,
            service.device_type,
            service.device_model,
            service.issue_description[:50],
            service.preferred_date,
            service.status,
            service.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response


@admin_required
def service_detail(request, service_id):
    """View service booking details"""
    service = get_object_or_404(ServiceBooking, id=service_id)
    
    context = {'service': service}
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/service_detail.html', context)


@require_POST
@admin_required
def assign_staff(request, service_id):
    """Assign staff to service"""
    service = get_object_or_404(ServiceBooking, id=service_id)
    staff_id = request.POST.get('staff_id')
    
    if staff_id:
        staff = get_object_or_404(User, id=staff_id, role='STAFF')
        service.assigned_staff = staff
        service.status = 'ASSIGNED'
        service.save()
        
        # Create staff task
        StaffTask.objects.create(
            staff=staff,
            task_type='SERVICE',
            service=service,
            assigned_by=User.objects.get(id=request.session['user_id'])
        )
        
        messages.success(request, f'Staff {staff.email} assigned')
    
    return redirect('admin_panel:service_detail', service_id=service.id)


@admin_required
def inventory_list(request):
    """List inventory with low stock alerts"""
    inventory = Inventory.objects.select_related('product').all()
    
    low_stock = request.GET.get('low_stock')
    if low_stock:
        inventory = inventory.filter(quantity__lte=F('low_stock_threshold'))
    
    context = {
        'inventory': inventory,
        'low_stock_filter': low_stock,
    }
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/inventory.html', context)


@admin_required
def category_list(request):
    """List all categories"""
    categories = Category.objects.all().order_by('order', 'name')
    products = Product.objects.all()
    parent_categories = categories.filter(parent=None)
    main_categories_count = parent_categories.count()
    
    context = {
        'categories': categories,
        'total_products': products.count(),
        'main_categories_count': main_categories_count,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/categories.html', context)


@admin_required
def category_create(request):
    """Create new category"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        parent_id = request.POST.get('parent')
        order = request.POST.get('order', 0)
        
        if not name:
            messages.error(request, 'Category name is required')
            return redirect('admin_panel:category_create')
        
        category = Category.objects.create(
            name=name,
            slug=slugify(name),
            description=description,
            parent_id=parent_id if parent_id else None,
            order=order
        )
        
        # Handle image upload
        if 'image' in request.FILES:
            category.image = request.FILES['image']
            category.save()
        
        messages.success(request, f'Category "{category.name}" created successfully')
        return redirect('admin_panel:categories')
    
    categories = Category.objects.filter(parent__isnull=True)
    context = {
        'categories': categories,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/category_form.html', context)


@admin_required
def category_edit(request, category_id):
    """Edit category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.parent_id = request.POST.get('parent') or None
        category.order = request.POST.get('order', 0)
        category.slug = slugify(category.name)
        
        if 'image' in request.FILES:
            category.image = request.FILES['image']
        
        category.save()
        
        messages.success(request, f'Category "{category.name}" updated successfully')
        return redirect('admin_panel:categories')
    
    categories = Category.objects.exclude(id=category_id).filter(parent__isnull=True)
    context = {
        'category': category,
        'categories': categories,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/category_form.html', context)


@admin_required
def category_delete(request, category_id):
    """Delete category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully')
        return redirect('admin_panel:categories')
    
    context = {
        'category': category,
        'product_count': category.products.count(),
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/category_confirm_delete.html', context)


@require_POST
@admin_required
def update_inventory(request, inventory_id):
    """Update inventory quantity"""
    inventory = get_object_or_404(Inventory, id=inventory_id)
    quantity = int(request.POST.get('quantity', 0))
    reason = request.POST.get('reason', 'Admin adjustment')
    
    from store.models import InventoryHistory
    from core.enums import InventoryChangeType
    
    old_quantity = inventory.quantity
    inventory.quantity = quantity
    inventory.save()
    
    InventoryHistory.objects.create(
        inventory=inventory,
        old_quantity=old_quantity,
        new_quantity=quantity,
        change_type=InventoryChangeType.ADJUSTMENT,
        changed_by=User.objects.get(id=request.session['user_id']),
        notes=reason
    )
    
    messages.success(request, 'Inventory updated')
    return redirect('admin_panel:inventory')


@admin_required
def reports_view(request):
    """View reports dashboard"""
    context = {}
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/reports.html', context)


@admin_required
def reports(request):
    """Display reports page"""
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    # Get all reports for the table
    recent_reports = SystemReport.objects.all().order_by('-created_at')[:20]
    
    # Get stats for cards
    total_sales = Order.objects.filter(payment_status='PAID').aggregate(Sum('total'))['total__sum'] or 0
    if isinstance(total_sales, Decimal):
        total_sales = float(total_sales)
    
    total_orders = Order.objects.filter(payment_status='PAID').count()
    total_customers = User.objects.filter(role='CUSTOMER').count()
    
    # Calculate conversion rate (example)
    conversion_rate = 15
    
    context = {
        'recent_reports': recent_reports,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'conversion_rate': conversion_rate,
    }
    return render(request, 'admin_panel/reports.html', context)


def generate_report(request):
    """Generate a report"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        period_start = request.POST.get('period_start')
        period_end = request.POST.get('period_end')
        
        # Helper to convert Decimal to float
        def convert_decimal(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, dict):
                return {k: convert_decimal(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_decimal(i) for i in obj]
            return obj
        
        # Generate report data based on type
        data = {}
        
        if report_type == 'SALES':
            orders = Order.objects.filter(
                created_at__date__gte=period_start,
                created_at__date__lte=period_end,
                payment_status='PAID'
            )
            
            total_revenue = orders.aggregate(Sum('total'))['total__sum'] or 0
            
            data = {
                'total_orders': orders.count(),
                'total_revenue': float(total_revenue) if isinstance(total_revenue, Decimal) else total_revenue,
                'period_start': period_start,
                'period_end': period_end,
                'orders': [
                    {
                        'order_number': order.order_number,
                        'total': float(order.total),
                        'status': order.status,
                        'created_at': order.created_at.strftime('%Y-%m-%d')
                    }
                    for order in orders[:100]  # Limit to 100 orders
                ]
            }
        
        elif report_type == 'INVENTORY':
            inventory_items = Inventory.objects.select_related('product').all()
            
            data = {
                'total_products': Product.objects.filter(status='ACTIVE').count(),
                'low_stock': inventory_items.filter(quantity__lte=F('low_stock_threshold')).count(),
                'out_of_stock': inventory_items.filter(quantity=0).count(),
                'total_stock': inventory_items.aggregate(Sum('quantity'))['quantity__sum'] or 0,
                'period_start': period_start,
                'period_end': period_end,
                'inventory': [
                    {
                        'product_name': item.product.name,
                        'quantity': item.quantity,
                        'available': item.available,
                        'low_stock_threshold': item.low_stock_threshold
                    }
                    for item in inventory_items[:100]
                ]
            }
        
        elif report_type == 'STAFF':
            staff_members = User.objects.filter(role='STAFF')
            staff_data = []
            
            for staff in staff_members:
                assigned_services = ServiceBooking.objects.filter(
                    assigned_staff=staff,
                    created_at__date__gte=period_start,
                    created_at__date__lte=period_end
                )
                completed_services = assigned_services.filter(status='COMPLETED')
                
                staff_data.append({
                    'name': staff.full_name,
                    'email': staff.email,
                    'assigned_services': assigned_services.count(),
                    'completed_services': completed_services.count()
                })
            
            data = {
                'total_staff': staff_members.count(),
                'period_start': period_start,
                'period_end': period_end,
                'staff': staff_data
            }
        
        elif report_type == 'CUSTOMER':
            customers = User.objects.filter(role='CUSTOMER')
            customer_data = []
            
            for customer in customers[:100]:
                orders = Order.objects.filter(user=customer, payment_status='PAID')
                total_spent = orders.aggregate(Sum('total'))['total__sum'] or 0
                
                customer_data.append({
                    'name': customer.full_name,
                    'email': customer.email,
                    'total_orders': orders.count(),
                    'total_spent': float(total_spent) if isinstance(total_spent, Decimal) else total_spent
                })
            
            data = {
                'total_customers': customers.count(),
                'new_customers': customers.filter(
                    date_joined__date__gte=period_start,
                    date_joined__date__lte=period_end
                ).count(),
                'period_start': period_start,
                'period_end': period_end,
                'customers': customer_data
            }
        
        elif report_type == 'FINANCIAL':
            orders = Order.objects.filter(
                created_at__date__gte=period_start,
                created_at__date__lte=period_end,
                payment_status='PAID'
            )
            total_revenue = orders.aggregate(Sum('total'))['total__sum'] or 0
            total_discount = orders.aggregate(Sum('discount'))['discount__sum'] or 0
            total_tax = orders.aggregate(Sum('tax'))['tax__sum'] or 0
            
            data = {
                'total_revenue': float(total_revenue) if isinstance(total_revenue, Decimal) else total_revenue,
                'total_discount': float(total_discount) if isinstance(total_discount, Decimal) else total_discount,
                'total_tax': float(total_tax) if isinstance(total_tax, Decimal) else total_tax,
                'total_orders': orders.count(),
                'period_start': period_start,
                'period_end': period_end,
            }
        
        # Convert any Decimal in data to float
        data = convert_decimal(data)
        
        # Get user
        user = User.objects.get(id=request.session['user_id'])
        
        # Create report
        SystemReport.objects.create(
            report_type=report_type,
            title=f"{dict(ReportType.choices).get(report_type, report_type)} Report - {period_start} to {period_end}",
            data=data,
            generated_by=user,
            period_start=period_start,
            period_end=period_end
        )
        
        messages.success(request, f'{report_type} report generated successfully')
        return redirect('admin_panel:reports')
    
    return redirect('admin_panel:reports')


def report_detail(request, report_id):
    if not request.session.get('user_id'):
        return redirect('accounts:login')

    report = get_object_or_404(SystemReport, id=report_id)

    data = report.data or {}

    # 🔥 FORCE CLEAN JSON FORMAT
    if report.report_type == 'SALES':
        orders = data.get('orders', [])
        status = data.get('orders_by_status', [])

        clean_orders = []
        for o in orders:
            clean_orders.append({
                "created_at": str(o.get("created_at")),
                "total": float(o.get("total", 0))
            })

        clean_status = []
        for s in status:
            clean_status.append({
                "status": str(s.get("status")),
                "count": int(s.get("count", 0))
            })

        data['orders'] = clean_orders
        data['orders_by_status'] = clean_status

    report_json = json.dumps(data)

    return render(request, 'admin_panel/report_detail.html', {
        'report': report,
        'report_json': report_json
    })


@admin_required
def announcements(request):
    """Manage announcements"""
    announcements = Announcement.objects.all().order_by('-created_at')
    
    context = {'announcements': announcements}
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/announcements.html', context)


@admin_required
def create_announcement(request):
    """Create new announcement"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        announcement_type = request.POST.get('announcement_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        target_roles = request.POST.getlist('target_roles')
        
        Announcement.objects.create(
            title=title,
            content=content,
            announcement_type=announcement_type,
            start_date=start_date,
            end_date=end_date,
            target_roles=target_roles
        )
        
        messages.success(request, 'Announcement created')
        return redirect('admin_panel:announcements')
    context = {}
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/create_announcement.html',context)


@admin_required
def edit_announcement(request, announcement_id):
    """Edit announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if request.method == 'POST':
        # Update announcement
        announcement.title = request.POST.get('title')
        announcement.content = request.POST.get('content')
        announcement.announcement_type = request.POST.get('announcement_type')
        announcement.start_date = request.POST.get('start_date')
        announcement.end_date = request.POST.get('end_date')
        
        # Clear existing target roles and set new ones
        announcement.target_roles.clear()
        target_roles = request.POST.getlist('target_roles')
        if target_roles:
            for role in target_roles:
                announcement.target_roles.append(role)
        else:
            # If no roles selected, show to everyone
            announcement.target_roles = ['CUSTOMER', 'STAFF', 'ADMIN']
        
        announcement.save()
        
        messages.success(request, f'Announcement "{announcement.title}" updated successfully')
        return redirect('admin_panel:announcements')
    
    context = {
        'announcement': announcement,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/edit_announcement.html', context)


@admin_required
def delete_announcement(request, announcement_id):
    """Delete announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    title = announcement.title
    announcement.delete()
    messages.success(request, f'Announcement "{title}" deleted successfully')
    return redirect('admin_panel:announcements')


@admin_required
def system_settings(request):
    """System settings"""
    from core.models import SystemConfig
    
    # Get all configs as dictionary
    configs = {config.config_key: config.config_value for config in SystemConfig.objects.all()}
    
    if request.method == 'POST':
        # Process all form fields
        for key, value in request.POST.items():
            if key.startswith('config_'):
                config_key = key.replace('config_', '')
                
                # Handle checkbox values (they send 'on' when checked)
                if value == 'on':
                    value = 'True'
                elif value == '' and key not in request.POST:
                    value = 'False'
                
                config, created = SystemConfig.objects.get_or_create(config_key=config_key)
                config.config_value = value
                config.save()
        
        # Handle checkboxes that weren't sent (unchecked)
        checkbox_fields = [
            'config_send_whatsapp', 'config_send_sms', 'config_send_email',
            'config_order_confirmation', 'config_maintenance_mode', 'config_allow_registration'
        ]
        
        for checkbox in checkbox_fields:
            if checkbox not in request.POST:
                config_key = checkbox.replace('config_', '')
                config, created = SystemConfig.objects.get_or_create(config_key=config_key)
                config.config_value = 'False'
                config.save()
        
        messages.success(request, 'Settings saved successfully')
        return redirect('admin_panel:settings')
    
    context = {
        'configs': configs,
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'admin_panel/settings.html', context)


@csrf_exempt
@admin_required
def clear_cache(request):
    """Clear system cache"""
    if request.method == 'POST':
        try:
            from django.core.cache import cache
            cache.clear()
            return JsonResponse({'success': True, 'message': 'Cache cleared successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)


@csrf_exempt
@admin_required
def clear_logs(request):
    """Clear system logs older than 30 days"""
    if request.method == 'POST':
        try:
            from core.models import ActivityLog
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff_date = timezone.now() - timedelta(days=30)
            deleted_count = ActivityLog.objects.filter(created_at__lt=cutoff_date).delete()
            
            return JsonResponse({
                'success': True, 
                'message': f'Cleared {deleted_count[0]} log entries older than 30 days'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)


@admin_required
def alerts(request):
    """View system alerts"""
    alerts = AdminAlert.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        alert_id = request.POST.get('mark_read')
        if alert_id:
            alert = get_object_or_404(AdminAlert, id=alert_id)
            user = User.objects.get(id=request.session['user_id'])
            alert.read_by.add(user)
            messages.success(request, 'Alert marked as read')
    
    context = {'alerts': alerts}
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'admin_panel/alerts.html', context)


def service_edit(request, service_id):
    """Edit service booking"""
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    from staff.models import ServiceBooking
    from accounts.models import User
    
    service = get_object_or_404(ServiceBooking, id=service_id)
    
    if request.method == 'POST':
        service.device_type = request.POST.get('device_type')
        service.device_model = request.POST.get('device_model')
        service.issue_description = request.POST.get('issue_description')
        service.preferred_date = request.POST.get('preferred_date')
        service.preferred_time_slot = request.POST.get('preferred_time_slot')
        service.status = request.POST.get('status')
        service.technician_notes = request.POST.get('technician_notes', '')
        
        assigned_staff_id = request.POST.get('assigned_staff')
        if assigned_staff_id:
            service.assigned_staff_id = assigned_staff_id
        else:
            service.assigned_staff = None
            
        service.save()
        messages.success(request, 'Service updated successfully')
        return redirect('admin_panel:service_detail', service_id=service.id)
    
    staff_members = User.objects.filter(role='STAFF')
    
    context = {
        'service': service,
        'staff_members': staff_members,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/service_edit.html', context)


def update_service_cost(request, service_id):
    """Update service cost"""
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    from staff.models import ServiceBooking
    
    service = get_object_or_404(ServiceBooking, id=service_id)
    
    if request.method == 'POST':
        final_cost = request.POST.get('final_cost')
        if final_cost:
            service.final_cost = final_cost
            service.save()
            messages.success(request, f'Service cost updated to ₹{final_cost}')
        return redirect('admin_panel:service_detail', service_id=service.id)
    
    context = {
        'service': service,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/update_cost.html', context)


@admin_required
def mark_all_alerts_read(request):
    """Mark all alerts as read for current user"""
    if request.method == 'POST':
        user = User.objects.get(id=request.session['user_id'])
        alerts = AdminAlert.objects.filter(is_read=False)
        for alert in alerts:
            alert.read_by.add(user)
        alerts.update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


@admin_required
def department_list(request):
    """List all departments"""
    departments = Department.objects.all().order_by('order', 'name')
    
    for dept in departments:
        dept.staff_count = StaffDepartment.objects.filter(department=dept).count()
        dept.task_count = StaffTask.objects.filter(
            staff__staff_departments__department=dept,
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).count()
        dept.service_count = ServiceBooking.objects.filter(
            assigned_staff__staff_departments__department=dept,
            status__in=['REQUESTED', 'ASSIGNED', 'IN_PROGRESS']
        ).count()
    
    context = {
        'departments': departments,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/departments/list.html', context)


@admin_required
def department_create(request):
    """Create new department"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', 'fas fa-building')
        color = request.POST.get('color', '#6366f1')
        order = request.POST.get('order', 0)
        
        department = Department.objects.create(
            name=name,
            slug=slugify(name),
            description=description,
            icon=icon,
            color=color,
            order=order,
            is_active=True
        )
        
        messages.success(request, f'Department "{name}" created successfully')
        return redirect('admin_panel:department_list')
    
    context = {'base_template': 'admin_panel/base.html'}
    return render(request, 'admin_panel/departments/form.html', context)


@admin_required
def department_edit(request, pk):
    """Edit department"""
    department = get_object_or_404(Department, id=pk)
    
    if request.method == 'POST':
        department.name = request.POST.get('name')
        department.description = request.POST.get('description', '')
        department.icon = request.POST.get('icon', 'fas fa-building')
        department.color = request.POST.get('color', '#6366f1')
        department.order = request.POST.get('order', 0)
        department.is_active = request.POST.get('is_active') == 'on'
        department.slug = slugify(department.name)
        department.save()
        
        messages.success(request, f'Department "{department.name}" updated successfully')
        return redirect('admin_panel:department_list')
    
    context = {
        'department': department,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/departments/form.html', context)


@admin_required
def department_delete(request, pk):
    """Delete department"""
    department = get_object_or_404(Department, id=pk)
    
    if request.method == 'POST':
        name = department.name
        department.delete()
        messages.success(request, f'Department "{name}" deleted successfully')
        return redirect('admin_panel:department_list')
    
    context = {
        'department': department,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/departments/delete.html', context)


@admin_required
def staff_by_department(request, dept_slug):
    """Filter staff by department"""
    department = get_object_or_404(Department, slug=dept_slug)
    staff_ids = StaffDepartment.objects.filter(department=department).values_list('staff_id', flat=True)
    staff_members = User.objects.filter(id__in=staff_ids, role='STAFF')
    
    # Get task and service counts
    for staff in staff_members:
        staff.task_count = StaffTask.objects.filter(
            staff=staff,
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).count()
        staff.service_count = ServiceBooking.objects.filter(
            assigned_staff=staff,
            status__in=['REQUESTED', 'ASSIGNED', 'IN_PROGRESS']
        ).count()
    
    context = {
        'department': department,
        'staff_members': staff_members,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/staff_by_dept.html', context)


@admin_required
def department_report(request, dept_slug):
    """Department wise report"""
    department = get_object_or_404(Department, slug=dept_slug)
    staff_ids = StaffDepartment.objects.filter(department=department).values_list('staff_id', flat=True)
    
    # Statistics
    total_staff = staff_ids.count()
    total_tasks = StaffTask.objects.filter(staff_id__in=staff_ids).count()
    completed_tasks = StaffTask.objects.filter(staff_id__in=staff_ids, status='COMPLETED').count()
    pending_tasks = StaffTask.objects.filter(staff_id__in=staff_ids, status__in=['ASSIGNED', 'IN_PROGRESS']).count()
    total_services = ServiceBooking.objects.filter(assigned_staff_id__in=staff_ids).count()
    completed_services = ServiceBooking.objects.filter(assigned_staff_id__in=staff_ids, status='COMPLETED').count()
    
    context = {
        'department': department,
        'total_staff': total_staff,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'total_services': total_services,
        'completed_services': completed_services,
        'completion_rate': int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0,
        'base_template': 'admin_panel/base.html'
    }
    return render(request, 'admin_panel/departments/report.html', context)