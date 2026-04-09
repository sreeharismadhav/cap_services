from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
import json
import random
import string
from .models import Cart, CartItem, Order, OrderItem, Coupon, CouponUsage, CouponType, Payment, Invoice
from store.models import Product
from accounts.models import User, UserAddress
from core.utils import generate_order_number, log_activity, generate_upi_qr
from core.views import get_base_template
from .forms import CartAddForm, CheckoutForm, CouponForm
from django.template.loader import render_to_string


def generate_booking_number():
    """Generate unique booking number for service"""
    prefix = 'SVC'
    timestamp = timezone.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{timestamp}{random_str}"


def payment_page(request, order_id):
    """Display payment page"""
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    order = get_object_or_404(Order, id=order_id, user=user)
    
    if order.payment_status == 'PAID':
        messages.info(request, 'Order already paid')
        return redirect('orders:order_detail', order_id=order.id)
    
    upi_id = 'sreeharishambhu1971-1@okaxis'  # Change to your UPI ID
    
    # Generate QR code dynamically
    qr_code_base64 = generate_upi_qr(
        upi_id=upi_id,
        amount=float(order.total),
        order_number=order.order_number,
        name="CAP Services"
    )
    
    context = {
        'order': order,
        'amount': order.total,
        'upi_id': upi_id,
        'qr_code': qr_code_base64,  # This will always work
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'orders/payment.html', context)

def payment_initiate(request, order_id):
    """Initiate payment - creates payment record"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    user = User.objects.get(id=request.session['user_id'])
    order = get_object_or_404(Order, id=order_id, user=user)
    
    if order.payment_status == 'PAID':
        return JsonResponse({'error': 'Already paid'}, status=400)
    
    Payment.objects.filter(order=order, status='PENDING').delete()
    
    transaction_id = f"UPI_{order.order_number}_{int(timezone.now().timestamp())}"
    
    payment = Payment.objects.create(
        order=order,
        payment_method='UPI',
        transaction_id=transaction_id,
        amount=order.total,
        status='PENDING',
        gateway_response={'initiated_at': str(timezone.now())}
    )
    
    request.session['current_payment_id'] = payment.id
    request.session['current_order_id'] = order.id
    
    return JsonResponse({
        'success': True,
        'payment_id': payment.id,
        'amount': float(order.total),
        'order_number': order.order_number
    })

def invoice_pdf(request, order_id):
    """Display invoice page - user can print to PDF"""
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    user_role = request.session.get('user_role')
    
    if user_role == 'ADMIN':
        order = get_object_or_404(Order, id=order_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=user)
    
    # Get or create invoice
    invoice, created = Invoice.objects.get_or_create(
        order=order,
        defaults={'invoice_number': f"INV{order.id}{order.created_at.strftime('%y%m%d')}"}
    )
    
    context = {
        'order': order,
        'invoice': invoice,
        'company_name': 'CAP Services',
        'company_email': 'capservicers@gmail.com',
        'company_phone': '7510158899',
    }
    
    return render(request, 'orders/invoice_template.html', context)

@csrf_exempt
def payment_verify(request):
    """Verify payment - user provides UPI transaction ID"""
    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        user_transaction_id = request.POST.get('transaction_id')
        upi_id = request.POST.get('upi_id', '')
        
        payment = get_object_or_404(Payment, id=payment_id)
        order = payment.order
        
        if order.payment_status == 'PAID':
            messages.warning(request, 'Order already paid')
            return redirect('orders:order_detail', order_id=order.id)
        
        payment.status = 'PAID'
        payment.transaction_id = user_transaction_id
        payment.payment_date = timezone.now()
        payment.gateway_response = {
            'verified': True,
            'verified_at': str(timezone.now()),
            'user_upi_id': upi_id,
            'user_transaction_id': user_transaction_id
        }
        payment.save()
        
        order.payment_status = 'PAID'
        order.save()
        
        request.session.pop('current_payment_id', None)
        request.session.pop('current_order_id', None)
        
        log_activity(order.user, f'PAYMENT_SUCCESS_{order.order_number}', request=request)
        
        messages.success(request, f'Payment recorded! Transaction ID: {user_transaction_id}')
        return redirect('orders:payment_success', order_id=order.id)
    
    return redirect('orders:cart_detail')


def payment_success(request, order_id):
    """Payment success page"""
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    order = get_object_or_404(Order, id=order_id, user=user)
    payment = Payment.objects.filter(order=order, status='PAID').first()
    
    context = {
        'order': order,
        'payment': payment,
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'orders/payment_success.html', context)


def payment_failed(request, order_id):
    """Payment failed page"""
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    order = get_object_or_404(Order, id=order_id, user=user)
    payment = Payment.objects.filter(order=order, status='FAILED').first()
    
    context = {
        'order': order,
        'payment': payment,
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'orders/payment_failed.html', context)


def payment_retry(request, order_id):
    """Retry payment"""
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    order = get_object_or_404(Order, id=order_id, user=user)
    
    if order.payment_status == 'PAID':
        messages.info(request, 'Order already paid')
        return redirect('orders:order_detail', order_id=order.id)
    
    Payment.objects.filter(order=order, status='PENDING').delete()
    
    transaction_id = f"UPI_{order.order_number}_{int(timezone.now().timestamp())}"
    
    Payment.objects.create(
        order=order,
        payment_method='UPI',
        transaction_id=transaction_id,
        amount=order.total,
        status='PENDING',
        gateway_response={'retry': True, 'initiated_at': str(timezone.now())}
    )
    
    messages.info(request, 'Please complete the payment')
    return redirect('orders:payment_page', order_id=order.id)


def cart_detail(request):
    if request.session.get('user_id'):
        user = User.objects.get(id=request.session['user_id'])
        cart, created = Cart.objects.get_or_create(user=user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_id=session_id)
    
    context = {'cart': cart}
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'orders/cart.html', context)


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, status='ACTIVE')
    form = CartAddForm(request.POST)
    
    if form.is_valid():
        quantity = form.cleaned_data['quantity']
        
        if product.inventory.available < quantity:
            messages.error(request, 'Not enough stock')
            return redirect('store:product_detail', slug=product.slug)
        
        if request.session.get('user_id'):
            user = User.objects.get(id=request.session['user_id'])
            cart, created = Cart.objects.get_or_create(user=user)
        else:
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_id=session_id)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'price': product.current_price}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        product.inventory.reserve(quantity)
        
        messages.success(request, f'{product.name} added to cart')
    
    return redirect('orders:cart_detail')


@require_POST
def cart_remove(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    if cart_item.product:
        cart_item.product.inventory.release(cart_item.quantity)
    cart_item.delete()
    
    messages.success(request, 'Item removed from cart')
    return redirect('orders:cart_detail')


@require_POST
def cart_update(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    data = json.loads(request.body)
    quantity = int(data.get('quantity', 1))
    
    if quantity <= 0:
        cart_item.delete()
        return JsonResponse({'status': 'removed'})
    
    if cart_item.product:
        if cart_item.product.inventory.available + cart_item.quantity < quantity:
            return JsonResponse({'status': 'error', 'message': 'Not enough stock'}, status=400)
        
        diff = quantity - cart_item.quantity
        if diff > 0:
            cart_item.product.inventory.reserve(diff)
        elif diff < 0:
            cart_item.product.inventory.release(-diff)
    
    cart_item.quantity = quantity
    cart_item.save()
    
    return JsonResponse({
        'status': 'success',
        'subtotal': float(cart_item.subtotal),
        'cart_total': float(cart_item.cart.total),
        'item_count': cart_item.cart.item_count
    })


def checkout(request):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    cart = Cart.objects.get(user=user)
    addresses = UserAddress.objects.filter(user=user).select_related('address')
    
    if cart.item_count == 0:
        messages.error(request, 'Your cart is empty')
        return redirect('store:product_list')
    
    # Check if cart has products only (no services in this cart)
    has_products = any(item.product is not None for item in cart.items.all())
    
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')
        notes = request.POST.get('notes', '')
        
        if not address_id:
            messages.error(request, 'Please select a delivery address')
            return redirect('orders:checkout')
        
        try:
            user_address = UserAddress.objects.get(id=address_id, user=user)
        except UserAddress.DoesNotExist:
            messages.error(request, 'Invalid address')
            return redirect('orders:checkout')
        
        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                user=user,
                shipping_address=user_address,
                subtotal=cart.subtotal,
                discount=cart.discount_total,
                total=cart.total,
                notes=notes,
                payment_status='PENDING'
            )
            
            # Apply coupon if used
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.discount_total
                order.save()
                
                CouponUsage.objects.create(
                    coupon=cart.coupon,
                    user=user,
                    order=order,
                    discount_amount=cart.discount_total
                )
                cart.coupon.used_count += 1
                cart.coupon.save()
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.price
                )
                
                # Deduct stock for products
                if cart_item.product:
                    cart_item.product.inventory.deduct(cart_item.quantity)
            
            # Clear cart
            cart.clear()
            
            # Handle payment
            if payment_method == 'COD':
                messages.error(request, 'COD is only available for services. Please pay online.')
                return redirect('orders:checkout')
            else:
                return redirect('orders:payment_page', order_id=order.id)
    
    context = {
        'cart': cart,
        'addresses': addresses,
        'has_products': has_products,
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'orders/checkout.html', context)


def order_detail(request, order_id):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    order = get_object_or_404(Order, id=order_id, user=user)
    
    context = {
        'order': order,
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'orders/order_detail.html', context)


def order_list(request):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    orders = Order.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'orders': orders,
        'base_template': get_base_template(request.session.get('user_role'))
    }
    return render(request, 'orders/order_list.html', context)


@require_POST
def apply_coupon(request):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Login required'}, status=401)
    
    user = User.objects.get(id=request.session['user_id'])
    cart = Cart.objects.get(user=user)
    form = CouponForm(request.POST)
    
    if form.is_valid():
        code = form.cleaned_data['code']
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
            
            if not coupon.is_valid:
                return JsonResponse({'error': 'Coupon expired or used'})
            
            if cart.subtotal < coupon.minimum_order:
                return JsonResponse({'error': f'Minimum order ₹{coupon.minimum_order} required'})
            
            cart.coupon = coupon
            if coupon.discount_type == CouponType.PERCENT:
                discount = (cart.subtotal * coupon.discount_value / 100)
                if coupon.maximum_discount:
                    discount = min(discount, coupon.maximum_discount)
            else:
                discount = min(coupon.discount_value, cart.subtotal)
            
            cart.coupon_discount = discount
            cart.save()
            
            return JsonResponse({
                'success': True,
                'discount': float(discount),
                'total': float(cart.total)
            })
            
        except Coupon.DoesNotExist:
            return JsonResponse({'error': 'Invalid coupon code'})
    
    return JsonResponse({'error': 'Invalid code'}, status=400)