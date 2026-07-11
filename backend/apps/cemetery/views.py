from django.conf import settings
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt


@xframe_options_exempt
def carte_embed(request):
    """Sert la page HTML embarquant Google Maps JS avec les marqueurs des
    caveaux. Appelée en iframe/WebView par le frontend Flet (page /carte).
    Les données des caveaux sont chargées côté client via fetch() sur les
    endpoints publics de l'API (/api/cimetiere/graves, /sections).

    @xframe_options_exempt retire le header X-Frame-Options (DENY par
    défaut sur tout le site) pour CETTE vue uniquement -- le frontend Flet
    est sur un sous-domaine Render différent (...-frontend.onrender.com),
    donc même "SAMEORIGIN" bloquerait l'embed. On restreint quand même
    l'autorisation via Content-Security-Policy: frame-ancestors, plus
    précis qu'une exemption totale.
    """
    context = {
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        "center_lat": settings.CEMETERY_CENTER_LAT,
        "center_lng": settings.CEMETERY_CENTER_LNG,
        "boundary_points": settings.CEMETERY_BOUNDARY_POINTS,
    }
    response = render(request, "cemetery/carte_embed.html", context)
    allowed_frame_ancestors = " ".join(
        ["'self'"] + [origin for origin in settings.MAP_EMBED_ALLOWED_ORIGINS if origin]
    )
    response["Content-Security-Policy"] = f"frame-ancestors {allowed_frame_ancestors}"
    return response