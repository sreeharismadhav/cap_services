from django import template
from django.utils import timezone
from core.utils import format_price, get_time_ago, mask_email, mask_phone

register = template.Library()


@register.filter
def currency(value):
    return format_price(value)


@register.filter
def timeago(value):
    if not value:
        return ''
    return get_time_ago(value)


@register.filter
def mask_email_filter(email):
    return mask_email(email)


@register.filter
def mask_phone_filter(phone):
    return mask_phone(phone)


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def current_year():
    return timezone.now().year


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)