from django.conf import settings
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt


@xframe_options_exempt
def carte_embed(request):
    """Sert la page HTML embarquant Google Maps JS avec les marqueurs des
    caveaux. Appelée en iframe/WebView par le frontend Flet (page /carte).
    Les données des caveaux sont chargées côté client via fetch() sur les
    endpoints publics de l'API (/api/cimetiere/graves, /sections).

    @xframe_options_exempt est nécessaire car le middleware Django applique
    X-Frame-Options: DENY par défaut sur toutes les réponses, ce qui bloque
    l'affichage dans l'iframe du WebView dès que le frontend et le backend
    sont déployés sur des origines différentes (ex: deux services Render
    distincts) — exactement le cas en production. Cette vue est la SEULE
    exemptée : le reste de l'application (API, admin) reste protégé contre
    le clickjacking.
    """
    context = {
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        "center_lat": settings.CEMETERY_CENTER_LAT,
        "center_lng": settings.CEMETERY_CENTER_LNG,
        "boundary_points": settings.CEMETERY_BOUNDARY_POINTS,
    }
    return render(request, "cemetery/carte_embed.html", context)
