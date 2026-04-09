from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db import connection
from store.models import Product, Category
from .utils import log_activity
import datetime

def get_base_template(user_role):
    """Return base template based on user role"""
    if user_role == 'ADMIN':
        return 'admin_panel/base.html'
    elif user_role == 'STAFF':
        return 'staff/base.html'
    else:
        return 'core/base.html'
    
def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.datetime.now().isoformat(),
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
        }, status=500)


def home(request):
    featured_products = Product.objects.filter(
        is_featured=True,
        status='ACTIVE'
    )[:8]
    
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    )
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'core/home.html', context)


def newsletter_subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # TODO: Save to newsletter model
            messages.success(request, 'Thank you for subscribing!')
        else:
            messages.error(request, 'Please enter a valid email')
    return redirect('core:home')