from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from api import api
from apps.cemetery.views import carte_embed

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("cimetiere/carte-embed/", carte_embed, name="carte_embed"),
]

# En mode développement (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# En production (DEBUG=False) sur Render
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)