import random
import string
import hashlib
import hmac
from django.conf import settings
from django.utils import timezone
import logging
import qrcode
from io import BytesIO
import base64
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_upi_qr(upi_id, amount, order_number, name="CAP Services"):
    """Generate UPI QR code as base64 image"""
    # Create UPI payment link
    upi_link = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&tn={order_number}&cu=INR"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_link)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


def generate_order_number():
    prefix = 'ORD'
    timestamp = timezone.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{timestamp}{random_str}"


def generate_invoice_number():
    prefix = 'INV'
    timestamp = timezone.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}{timestamp}{random_str}"


def generate_booking_number():
    prefix = 'SVC'
    timestamp = timezone.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{timestamp}{random_str}"


def generate_sku():
    prefix = 'PRD'
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}{random_str}"


def mask_email(email):
    if not email or '@' not in email:
        return email
    local, domain = email.split('@')
    if len(local) <= 2:
        return f"{local[0]}*@{domain}"
    return f"{local[0]}{'*' * (len(local)-2)}{local[-1]}@{domain}"


def mask_phone(phone):
    if not phone or len(phone) < 10:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def format_price(amount):
    if amount is None:
        return '₹0'
    return f"₹{amount:,.2f}"


def get_time_ago(dt):
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


def validate_indian_phone(phone):
    import re
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_pincode(pincode):
    import re
    pattern = r'^\d{6}$'
    return bool(re.match(pattern, pincode))


def log_activity(user, action, model_name=None, object_id=None, details=None, request=None):
    from core.models import ActivityLog
    
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        user_agent = request.META.get('HTTP_USER_AGENT')
    
    ActivityLog.objects.create(
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        user_role=user.role if user else None,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else '',
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent
    )