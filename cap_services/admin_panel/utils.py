from .models import AdminAlert
from accounts.models import User
from django.db.models import F

def create_admin_alert(title, message, alert_type='INFO', link=''):
    """Create an admin alert"""
    alert = AdminAlert.objects.create(
        title=title,
        message=message,
        alert_type=alert_type,
        link=link
    )
    return alert


def get_dashboard_stats():
    """Get dashboard statistics for admin panel"""
    from django.db.models import Sum, Count
    from django.utils import timezone
    from accounts.models import User
    from store.models import Product, Order, Inventory
    from staff.models import ServiceBooking
    
    today = timezone.now().date()
    
    return {
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
        'low_stock': Inventory.objects.filter(quantity__lte=F('low_stock_threshold')).count(),
        'pending_services': ServiceBooking.objects.filter(status='REQUESTED').count(),
    }