from django.conf import settings
from store.models import Category
from orders.models import Cart


def site_settings(request):
    return {
        'site_name': settings.SITE_NAME,
        'site_url': settings.SITE_URL,
        'site_email': settings.SITE_EMAIL,
        'site_phone': settings.SITE_PHONE,
        'debug': settings.DEBUG,
    }


def cart_count(request):
    cart_count = 0
    if request.session.get('user_id'):
        from accounts.models import User
        try:
            user = User.objects.get(id=request.session['user_id'])
            cart, created = Cart.objects.get_or_create(user=user)
            cart_count = cart.item_count
        except:
            pass
    
    return {'cart_count': cart_count}


def main_categories(request):
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    )[:8]
    
    return {'main_categories': categories}