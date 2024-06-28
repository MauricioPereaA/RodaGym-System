from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_url = reverse('acceso:acceso_live')
        if not request.user.is_authenticated and request.path != login_url:
            return redirect(settings.LOGIN_URL)
        response = self.get_response(request)
        return response