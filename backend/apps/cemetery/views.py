from django.conf import settings
from django.shortcuts import render


def carte_embed(request):
    """Sert la page HTML embarquant Google Maps JS avec les marqueurs des
    caveaux. Appelée en iframe/WebView par le frontend Flet (page /carte).
    Les données des caveaux sont chargées côté client via fetch() sur les
    endpoints publics de l'API (/api/cimetiere/graves, /sections)."""
    context = {
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        "center_lat": settings.CEMETERY_CENTER_LAT,
        "center_lng": settings.CEMETERY_CENTER_LNG,
        "boundary_points": settings.CEMETERY_BOUNDARY_POINTS,
    }
    return render(request, "cemetery/carte_embed.html", context)
