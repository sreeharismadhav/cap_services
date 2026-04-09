import re
from django.utils import timezone
from .utils import log_activity


class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exclude_urls = [
            r'^/static/',
            r'^/media/',
            r'^/health/',
        ]
    
    def __call__(self, request):
        response = self.get_response(request)
        
        if request.session.get('user_id') and response.status_code < 400:
            path = request.path
            for pattern in self.exclude_urls:
                if re.match(pattern, path):
                    return response
            
            from accounts.models import User
            try:
                user = User.objects.get(id=request.session['user_id'])
                log_activity(
                    user=user,
                    action=f'VIEW_{path.strip("/").upper().replace("/", "_")}',
                    request=request
                )
            except:
                pass
        
        return response


class LastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.session.get('user_id'):
            from accounts.models import User
            try:
                user = User.objects.get(id=request.session['user_id'])
                user.last_seen = timezone.now()
                user.save(update_fields=['last_seen'])
            except:
                pass
        
        return self.get_response(request)