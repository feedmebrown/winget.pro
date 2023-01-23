from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from core import admin

urlpatterns = [
    path('', include('winget.urls')),
    path('admin/', admin.site.urls)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)