from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from api import api
from apps.cemetery.views import carte_embed

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls), # C'est cette ligne qui gère déjà automatiquement /api/docs !
    path("cimetiere/carte-embed/", carte_embed, name="carte_embed"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)