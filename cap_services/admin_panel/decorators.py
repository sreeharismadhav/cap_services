from django.shortcuts import redirect
from django.http import JsonResponse
from functools import wraps


def admin_required(view_func):
    """Decorator to ensure user is admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_role = request.session.get('user_role')
        if not user_role:
            return redirect('accounts:login')
        if user_role != 'ADMIN':
            return JsonResponse({'error': 'Admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper