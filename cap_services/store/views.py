from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category, Product, Review
from orders.models import Cart, CartItem    
from core.views import get_base_template
from staff.models import ServiceBooking
from core.utils import log_activity
from .forms import ReviewForm
from django.utils import timezone
from .models import Category, Product, Review
from orders.models import Cart, CartItem
from .forms import ReviewForm
from core.views import get_base_template
import random
import string


def product_list(request, category_slug=None):
    category = None
    products = Product.objects.filter(status='ACTIVE')
    subcategories = []
    all_category_ids = []
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        
        # Get ALL category IDs (main category + all subcategories)
        all_category_ids = [category.id]
        
        # Get all child subcategories recursively
        def get_all_subcategories(cat):
            ids = []
            for child in cat.children.filter(is_active=True):
                ids.append(child.id)
                ids.extend(get_all_subcategories(child))
            return ids
        
        subcategory_ids = get_all_subcategories(category)
        all_category_ids.extend(subcategory_ids)
        
        # Get subcategory objects for display
        subcategories = Category.objects.filter(id__in=subcategory_ids, is_active=True)
        
        # Filter products from main category AND all subcategories
        products = products.filter(category__id__in=all_category_ids)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(specifications__icontains=search_query)
        )
    
    # Filter by price
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'category': category,
        'products': products,
        'subcategories': subcategories,
        'all_category_ids': all_category_ids,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, status='ACTIVE')
    related_products = Product.objects.filter(
        category=product.category, 
        status='ACTIVE'
    ).exclude(id=product.id)[:4]
    
    reviews = product.reviews.filter(is_approved=True)
    
    # Check if user can review
    user_review = None
    if request.session.get('user_id'):
        from accounts.models import User
        user = User.objects.get(id=request.session['user_id'])
        user_review = reviews.filter(user=user).first()
    
    # Handle review form
    if request.method == 'POST' and request.session.get('user_id'):
        form = ReviewForm(request.POST)
        if form.is_valid():
            from accounts.models import User
            user = User.objects.get(id=request.session['user_id'])
            
            # Check if already reviewed
            if not Review.objects.filter(product=product, user=user).exists():
                review = form.save(commit=False)
                review.product = product
                review.user = user
                review.save()
                messages.success(request, 'Review submitted successfully!')
                return redirect('store:product_detail', slug=slug)
            else:
                messages.error(request, 'You have already reviewed this product')
    else:
        form = ReviewForm()
    
    # Get cart count
    cart_count = 0
    if request.session.get('user_id'):
        from accounts.models import User
        user = User.objects.get(id=request.session['user_id'])
        try:
            cart = Cart.objects.get(user=user)
            cart_count = cart.item_count
        except Cart.DoesNotExist:
            pass
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'user_review': user_review,
        'form': form,
        'cart_count': cart_count,
    }
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'store/product_detail.html', context)


def categories(request):
    # Get all active parent categories (main categories)
    parent_categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True  # Only parent categories
    ).order_by('order', 'name')
    
    # For each parent category, prefetch children to avoid N+1 queries
    categories_with_children = parent_categories.prefetch_related('children')
    
    context = {
        'categories': categories_with_children,
    }
    return render(request, 'store/categories.html', context)


def search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query),
        status='ACTIVE'
    )[:20]
    
    context = {
        'query': query,
        'products': products,
    }
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'store/search.html', context)

def generate_booking_number():
    prefix = 'SVC'
    timestamp = timezone.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{timestamp}{random_str}"

def book_service(request):
    """Direct service booking page for customers"""
    if not request.session.get('user_id'):
        messages.error(request, 'Please login to book a service')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        booking = ServiceBooking.objects.create(
            user_id=request.session['user_id'],
            booking_number=generate_booking_number(),
            device_type=request.POST.get('device_type'),
            device_model=request.POST.get('device_model', ''),
            issue_description=request.POST.get('issue_description'),
            address_line1=request.POST.get('address_line1'),
            address_line2=request.POST.get('address_line2', ''),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            pincode=request.POST.get('pincode'),
            landmark=request.POST.get('landmark', ''),
            preferred_date=request.POST.get('preferred_date'),
            preferred_time_slot=request.POST.get('preferred_time_slot', ''),
            status='REQUESTED'
        )
        messages.success(request, f'Booking #{booking.booking_number} created!')
        return redirect('store:booking_success', booking_id=booking.id)
    
    return render(request, 'store/book_service.html', {
        'base_template': get_base_template(request.session.get('user_role'))
    })

def booking_success(request, booking_id):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    booking = get_object_or_404(ServiceBooking, id=booking_id, user_id=request.session['user_id'])
    return render(request, 'store/booking_success.html', {
        'booking': booking,
        'base_template': get_base_template(request.session.get('user_role'))
    })

def my_bookings(request):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    bookings = ServiceBooking.objects.filter(user_id=request.session['user_id']).order_by('-created_at')
    return render(request, 'store/my_bookings.html', {
        'bookings': bookings,
        'base_template': get_base_template(request.session.get('user_role')),
        'pending_count': bookings.filter(status='REQUESTED').count(),
        'completed_count': bookings.filter(status='COMPLETED').count(),
        'cancelled_count': bookings.filter(status='CANCELLED').count(),
    })

def booking_detail(request, booking_id):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    booking = get_object_or_404(ServiceBooking, id=booking_id, user_id=request.session['user_id'])
    return render(request, 'store/booking_detail.html', {
        'booking': booking,
        'base_template': get_base_template(request.session.get('user_role'))
    })

def cancel_booking(request, booking_id):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    if request.method == 'POST':
        booking = get_object_or_404(ServiceBooking, id=booking_id, user_id=request.session['user_id'])
        if booking.status == 'REQUESTED':
            booking.status = 'CANCELLED'
            booking.save()
            messages.success(request, 'Booking cancelled successfully')
    return redirect('store:booking_detail', booking_id=booking_id)