from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("health/", health_check),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('searchs/', include('searchs.urls')),
    path('booths/', include('booths.urls')),
    path('shows/', include('shows.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
