from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from api import api
from apps.cemetery.views import carte_embed

# On importe l'outil de rendu de documentation de Django Ninja
from ninja.openapi.views import openapi_view

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # ÉTAPE CLÉ : On force l'affichage de la documentation avec les CDN externes valides
    path("api/docs", openapi_view, {
        "api": api,
        "swagger_js": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        "swagger_css": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    }),
    
    path("api/", api.urls),
    path("cimetiere/carte-embed/", carte_embed, name="carte_embed"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)