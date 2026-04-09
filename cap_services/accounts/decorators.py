from django.shortcuts import redirect
from django.http import JsonResponse
from functools import wraps


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_role = request.session.get('user_role')
            if not user_role:
                return redirect('accounts:login')
            if user_role not in allowed_roles:
                return JsonResponse({'error': 'Permission denied'}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def customer_required(view_func):
    return role_required(['CUSTOMER'])(view_func)


def staff_required(view_func):
    return role_required(['STAFF'])(view_func)


def admin_required(view_func):
    return role_required(['ADMIN'])(view_func)