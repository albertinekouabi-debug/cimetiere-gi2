"""
Teste la CONSTRUCTION de chaque vue Flet contre le backend réel, sans
navigateur, ET simule le parcours complet Bouton -> Dialogue -> Remplissage
-> Soumission -> Fermeture pour les formulaires CRUD principaux, afin de
détecter les erreurs de câblage frontend -> API qu'une simple construction
de page ne révèle pas (les dialogues ne s'ouvrent que sur clic).
Ne remplace pas un test manuel dans un vrai navigateur, mais couvre la
majorité des régressions de logique Python côté frontend.
"""
import sys
import traceback
import asyncio

sys.path.insert(0, ".")

import flet as ft
from app.state.session_context import SessionContext
from app.services.api_client import ApiError


class FakePage:
    def __init__(self):
        self.views = []
        self.dialog = None
        self.route = "/"
        self.width = 1200  # desktop par défaut ; les tests responsive changent explicitement cette valeur
        self.client_storage = FakeClientStorage()
        self.show_drawer_calls = 0
        self.close_drawer_calls = 0

    def update(self):
        pass

    def go(self, route):
        self.route = route

    def launch_url(self, url):
        pass

    def show_dialog(self, dialog):
        dialog.open = True
        dialog.update = lambda: None  # nécessite une vraie connexion Flet ; neutralisé en test
        self.dialog = dialog

    def pop_dialog(self):
        if self.dialog is not None:
            self.dialog.open = False
        return self.dialog

    async def show_drawer(self):
        self.show_drawer_calls += 1

    async def close_drawer(self):
        self.close_drawer_calls += 1

    def run_task(self, handler, *args, **kwargs):
        return asyncio.run(handler(*args, **kwargs))


class FakeClientStorage:
    def __init__(self):
        self._data = {}

    def get(self, key):
        return self._data.get(key)

    def set(self, key, value):
        self._data[key] = value

    def remove(self, key):
        self._data.pop(key, None)


class FakeEvent:
    """Simule un ft.ControlEvent minimal pour déclencher les handlers on_click."""
    pass


FIELD_VALUES_BY_LABEL_KEYWORD = [
    ("mot de passe", "AutoTest1234!"),
    ("email", "auto.test@cimetiere.cg"),
    ("nom de la section", "Section Auto Test"),
    ("nom du bloc", "Bloc Auto Test"),
    ("nom complet", "Utilisateur Auto Test"),
    ("nom du défunt", "Ntsiba"),
    ("prénom du défunt", "Auto"),
    ("nom de la famille", "Famille Auto Test"),
    ("numéro du caveau", "AUTO-TEST-001"),
    ("contact famille", "+242060000099"),
    ("motif", "Motif de test automatisé"),
    ("description", "Description générée automatiquement"),
    ("superficie", "150"),
    ("montant supplémentaire", "0"),
    ("montant total", "100000"),
    ("montant", "50000"),
    ("numéro mtn momo", "242061234567"),
    ("date de décès", "2026-01-15"),
    ("date de début", "2026-01-01"),
    ("date planifiée", "2026-08-01"),
    ("date de paiement", "2026-01-20"),
    ("latitude", ""),
    ("longitude", ""),
    ("notes", ""),
]


def _walk_controls(root):
    """Parcourt récursivement l'arbre de contrôles Flet (Container.content,
    Column/Row.controls, AlertDialog.content/actions, DataTable.rows,
    DataRow.cells, DataCell.content)."""
    if root is None:
        return
    yield root
    for attr in ("content", "controls", "actions", "rows", "cells"):
        val = getattr(root, attr, None)
        if val is None:
            continue
        if isinstance(val, (list, tuple)):
            for item in val:
                yield from _walk_controls(item)
        else:
            yield from _walk_controls(val)


def _fill_and_submit_dialog(page: "FakePage", label: str):
    """Trouve le dialogue actuellement ouvert, remplit les champs texte
    d'après leur libellé, puis clique sur le bouton d'action principal
    (dernier bouton de dialog.actions). Retourne True si le dialogue s'est
    fermé (= sauvegarde réussie côté API)."""
    dialog = page.dialog
    if dialog is None:
        raise AssertionError(f"[{label}] Aucun dialogue n'a été ouvert par le bouton.")

    for ctrl in _walk_controls(dialog.content):
        if isinstance(ctrl, ft.TextField) and not ctrl.value:
            field_label = (ctrl.label or "").lower()
            for keyword, value in FIELD_VALUES_BY_LABEL_KEYWORD:
                if keyword in field_label:
                    ctrl.value = value
                    break

    if not dialog.actions:
        raise AssertionError(f"[{label}] Le dialogue n'a aucune action.")
    save_button = dialog.actions[-1]
    if save_button.on_click is None:
        raise AssertionError(f"[{label}] Le bouton de sauvegarde n'a pas de on_click.")
    save_button.on_click(FakeEvent())
    return not dialog.open


def _extract_text(content) -> str:
    """Extrait le texte affiché d'un contrôle `content`, qu'il s'agisse d'une
    chaîne brute (content=text) ou d'un contrôle ft.Text (content=ft.Text(text))
    — les deux formes coexistent dans le code selon les fichiers."""
    if isinstance(content, str):
        return content
    if isinstance(content, ft.Text) and isinstance(content.value, str):
        return content.value
    return ""


def _click_new_button(page: "FakePage", view, button_text_hint: str):
    """Trouve un bouton dont le texte contient `button_text_hint` dans la vue
    et déclenche son on_click."""
    for ctrl in _walk_controls(view):
        text = _extract_text(getattr(ctrl, "content", None))
        if text and button_text_hint.lower() in text.lower() and getattr(ctrl, "on_click", None):
            ctrl.on_click(FakeEvent())
            return True
    return False


def _click_icon_button(view, icon_const, occurrence: int = 0):
    """Trouve le N-ième IconButton portant l'icône donnée et déclenche son
    on_click (utilisé pour les icônes crayon/poubelle des tableaux)."""
    matches = [c for c in _walk_controls(view) if getattr(c, "icon", None) == icon_const and getattr(c, "on_click", None)]
    if occurrence < len(matches):
        matches[occurrence].on_click(FakeEvent())
        return True
    return False


def _click_text_button(view, text_hint: str):
    """Trouve un TextButton dont le contenu contient `text_hint` (utilisé
    pour Valider/Refuser/Archiver/Démarrer/Terminer/Confirmer)."""
    for ctrl in _walk_controls(view):
        if isinstance(ctrl, ft.TextButton):
            text = _extract_text(getattr(ctrl, "content", None))
            if text and text_hint.lower() in text.lower() and getattr(ctrl, "on_click", None):
                ctrl.on_click(FakeEvent())
                return True
    return False


def _click_last_dialog_action(page: "FakePage"):
    """Clique sur la dernière action du dialogue courant (bouton 'Confirmer'
    des confirm_dialog, ou bouton de sauvegarde des form_dialog)."""
    dialog = page.dialog
    if dialog is None or not dialog.actions:
        return False
    dialog.actions[-1].on_click(FakeEvent())
    return True


def _row_occurrence(items: list, target_id) -> int:
    """Retourne l'index de l'élément `target_id` dans `items`, correspondant
    à sa position réelle dans le DataTable (même ordre que l'API, puisque
    build_data_table n'effectue aucun tri supplémentaire côté frontend).
    Nécessaire car plusieurs enregistrements peuvent déjà exister au moment
    du test (créés par les scénarios précédents), rendant l'hypothèse
    'occurrence=0' non fiable."""
    for i, item in enumerate(items):
        if item["id"] == target_id:
            return i
    raise AssertionError(f"Élément {target_id} introuvable dans la liste pour déterminer sa position.")


def run_edit_delete_status_tests(page, ctx, fails):
    """Teste les parcours Édition, Suppression et transitions de statut
    (Valider/Refuser/Archiver/Démarrer/Terminer/Renouveler), en vérifiant
    l'effet réel en base via l'API après chaque action UI — pas seulement
    la fermeture du dialogue, qui ne prouve pas le succès (confirm_dialog se
    ferme même si l'appel API sous-jacent échoue)."""
    from app.pages.sections_page import build_sections_view
    from app.pages.blocs_page import build_blocs_view
    from app.pages.graves_page import build_graves_view
    from app.pages.reservations_page import build_reservations_view
    from app.pages.concessions_page import build_concessions_view
    from app.pages.paiements_page import build_paiements_view
    from app.pages.exhumations_page import build_exhumations_view
    from app.pages.users_page import build_users_view

    def check(name, fn):
        try:
            fn()
            print(f"[OK ] {name}")
        except Exception as e:
            print(f"[FAIL] {name} -> {type(e).__name__}: {e}")
            traceback.print_exc()
            fails.append(name)

    # ─── Sections : édition puis suppression ──────────────────────────────
    def test_section_edit_delete():
        s = ctx.cemetery.create_section({"nom": "Section EditDelete", "description": None, "superficie": None})
        current = ctx.cemetery.list_sections()
        idx = _row_occurrence(current, s["id"])
        view = build_sections_view(page, ctx)
        assert _click_icon_button(view, ft.Icons.EDIT_OUTLINED, occurrence=idx), "icône édition introuvable"
        assert _fill_and_submit_dialog(page, "edit section"), "la modification n'a pas abouti"
        updated = ctx.cemetery.list_sections()
        assert any(x["id"] == s["id"] and x["description"] == "Description générée automatiquement" for x in updated), "la modification n'a pas été persistée en base"
        current = ctx.cemetery.list_sections()
        idx = _row_occurrence(current, s["id"])
        view = build_sections_view(page, ctx)  # revue fraîche après modification
        assert _click_icon_button(view, ft.Icons.DELETE_OUTLINE, occurrence=idx), "icône suppression introuvable"
        _click_last_dialog_action(page)
        remaining = ctx.cemetery.list_sections()
        assert not any(x["id"] == s["id"] for x in remaining), "la suppression n'a pas été persistée en base"

    check("Édition + suppression : Section", test_section_edit_delete)

    # ─── Blocs : édition puis suppression ─────────────────────────────────
    def test_bloc_edit_delete():
        s = ctx.cemetery.create_section({"nom": "Section pour Bloc EditDelete", "description": None, "superficie": None})
        b = ctx.cemetery.create_bloc({"section_id": s["id"], "nom": "Bloc EditDelete"})
        current = ctx.cemetery.list_blocs()
        idx = _row_occurrence(current, b["id"])
        view = build_blocs_view(page, ctx)
        assert _click_icon_button(view, ft.Icons.EDIT_OUTLINED, occurrence=idx), "icône édition introuvable"
        assert _fill_and_submit_dialog(page, "edit bloc"), "la modification n'a pas abouti"
        current = ctx.cemetery.list_blocs()
        idx = _row_occurrence(current, b["id"])
        view = build_blocs_view(page, ctx)
        assert _click_icon_button(view, ft.Icons.DELETE_OUTLINE, occurrence=idx), "icône suppression introuvable"
        _click_last_dialog_action(page)
        remaining = ctx.cemetery.list_blocs()
        assert not any(x["id"] == b["id"] for x in remaining), "la suppression du bloc n'a pas été persistée"
        ctx.cemetery.delete_section(s["id"])

    check("Édition + suppression : Bloc", test_bloc_edit_delete)

    # ─── Caveaux : édition puis suppression ───────────────────────────────
    def test_grave_edit_delete():
        s = ctx.cemetery.create_section({"nom": "Section pour Caveau EditDelete", "description": None, "superficie": None})
        b = ctx.cemetery.create_bloc({"section_id": s["id"], "nom": "Bloc pour Caveau EditDelete"})
        g = ctx.cemetery.create_grave({"bloc_id": b["id"], "numero": "ED-001", "status": "libre"})
        current = ctx.cemetery.list_graves()
        idx = _row_occurrence(current, g["id"])
        view = build_graves_view(page, ctx)
        assert _click_icon_button(view, ft.Icons.EDIT_OUTLINED, occurrence=idx), "icône édition introuvable"
        assert _fill_and_submit_dialog(page, "edit grave"), "la modification n'a pas abouti"
        current = ctx.cemetery.list_graves()
        idx = _row_occurrence(current, g["id"])
        view = build_graves_view(page, ctx)
        assert _click_icon_button(view, ft.Icons.DELETE_OUTLINE, occurrence=idx), "icône suppression introuvable"
        _click_last_dialog_action(page)
        remaining = ctx.cemetery.list_graves()
        assert not any(x["id"] == g["id"] for x in remaining), "la suppression du caveau n'a pas été persistée"
        ctx.cemetery.delete_bloc(b["id"])
        ctx.cemetery.delete_section(s["id"])

    check("Édition + suppression : Caveau", test_grave_edit_delete)

    # ─── Réservations : valider puis archiver ─────────────────────────────
    def test_reservation_validate_archive():
        s = ctx.cemetery.create_section({"nom": "Section Résa Test", "description": None, "superficie": None})
        b = ctx.cemetery.create_bloc({"section_id": s["id"], "nom": "Bloc Résa Test"})
        g = ctx.cemetery.create_grave({"bloc_id": b["id"], "numero": "RESA-001", "status": "libre"})
        r = ctx.reservations.create({
            "grave_id": g["id"], "defunt_nom": "Test", "defunt_prenom": "Résa",
            "defunt_date_deces": "2026-01-01", "famille_nom": "Famille Test",
        })
        view = build_reservations_view(page, ctx)
        assert _click_text_button(view, "Valider"), "bouton Valider introuvable"
        updated = ctx.reservations.list()
        assert any(x["id"] == r["id"] and x["status"] == "validee" for x in updated), "la validation n'a pas été persistée"
        view = build_reservations_view(page, ctx)
        assert _click_text_button(view, "Archiver"), "bouton Archiver introuvable"
        updated = ctx.reservations.list()
        assert any(x["id"] == r["id"] and x["status"] == "archivee" for x in updated), "l'archivage n'a pas été persisté"
        ctx.reservations.delete(r["id"])
        ctx.cemetery.delete_grave(g["id"])
        ctx.cemetery.delete_bloc(b["id"])
        ctx.cemetery.delete_section(s["id"])

    check("Workflow : Réservation (valider + archiver)", test_reservation_validate_archive)

    # ─── Exhumations : démarrer puis terminer ─────────────────────────────
    def test_exhumation_status_flow():
        s = ctx.cemetery.create_section({"nom": "Section Exhum Statut", "description": None, "superficie": None})
        b = ctx.cemetery.create_bloc({"section_id": s["id"], "nom": "Bloc Exhum Statut"})
        g = ctx.cemetery.create_grave({"bloc_id": b["id"], "numero": "EXST-001", "status": "libre"})
        ctx.cemetery.create_defunt({"nom": "Test", "prenom": "ExhumStatut", "date_deces": "2026-01-01", "grave_id": g["id"]})
        ex = ctx.exhumations.create({"grave_id": g["id"], "motif": "Test statut"})
        view = build_exhumations_view(page, ctx)
        assert _click_text_button(view, "Démarrer"), "bouton Démarrer introuvable"
        updated = ctx.exhumations.list()
        assert any(x["id"] == ex["id"] and x["status"] == "en_cours" for x in updated), "le passage en_cours n'a pas été persisté"
        view = build_exhumations_view(page, ctx)
        assert _click_text_button(view, "Terminer"), "bouton Terminer introuvable"
        updated = ctx.exhumations.list()
        assert any(x["id"] == ex["id"] and x["status"] == "termine" for x in updated), "le passage termine n'a pas été persisté"
        ctx.exhumations.delete(ex["id"])
        ctx.cemetery.delete_bloc(b["id"])
        ctx.cemetery.delete_section(s["id"])

    check("Workflow : Exhumation (démarrer + terminer)", test_exhumation_status_flow)

    # ─── Concessions : renouvellement ──────────────────────────────────────
    def test_concession_renew():
        s = ctx.cemetery.create_section({"nom": "Section Concession Renew", "description": None, "superficie": None})
        b = ctx.cemetery.create_bloc({"section_id": s["id"], "nom": "Bloc Concession Renew"})
        g = ctx.cemetery.create_grave({"bloc_id": b["id"], "numero": "REN-001", "status": "libre"})
        c = ctx.concessions.create({
            "grave_id": g["id"], "famille_nom": "Famille Renew", "duree": "10_ans",
            "date_debut": "2026-01-01", "montant_total": 100000,
        })
        current = ctx.concessions.list()
        idx = _row_occurrence(current, c["id"])
        view = build_concessions_view(page, ctx)
        assert _click_icon_button(view, ft.Icons.EDIT_OUTLINED, occurrence=idx), "icône renouvellement introuvable"
        assert _fill_and_submit_dialog(page, "renew concession"), "le renouvellement n'a pas abouti"
        updated = ctx.concessions.list()
        match = next((x for x in updated if x["id"] == c["id"]), None)
        assert match is not None and match["date_fin"] == "2046-01-01", f"date de fin après renouvellement incorrecte : {match}"
        ctx.concessions.delete(c["id"])
        ctx.cemetery.delete_grave(g["id"])
        ctx.cemetery.delete_bloc(b["id"])
        ctx.cemetery.delete_section(s["id"])

    check("Workflow : Concession (renouvellement)", test_concession_renew)

    # ─── Utilisateurs : édition puis suppression ──────────────────────────
    def test_user_edit_delete():
        u = ctx.users.create({"email": "edituser.test@cimetiere.cg", "password": "TestUser1234!", "full_name": "User EditDelete", "role": "agent"})
        current = ctx.users.list()
        idx = _row_occurrence(current, u["id"])
        view = build_users_view(page, ctx)
        assert _click_icon_button(view, ft.Icons.EDIT_OUTLINED, occurrence=idx), "icône édition utilisateur introuvable"
        # Le formulaire d'édition pré-remplit "nom complet" avec la valeur
        # existante : le remplisseur de test ne doit PAS l'écraser (il ne
        # touche que les champs vides), donc on modifie explicitement ce
        # champ avant soumission pour vérifier que le changement est bien
        # transmis puis persisté par l'API.
        dialog = page.dialog
        assert dialog is not None, "le dialogue d'édition ne s'est pas ouvert"
        for ctrl in _walk_controls(dialog.content):
            if isinstance(ctrl, ft.TextField) and (ctrl.label or "").lower().startswith("nom complet"):
                ctrl.value = "Utilisateur Modifié Auto"
        assert _fill_and_submit_dialog(page, "edit user"), "la modification utilisateur n'a pas abouti"
        updated = ctx.users.list()
        match = next((x for x in updated if x["id"] == u["id"]), None)
        assert match is not None and match["full_name"] == "Utilisateur Modifié Auto", f"modification non persistée : {match}"
        current = ctx.users.list()
        idx = _row_occurrence(current, u["id"])
        view = build_users_view(page, ctx)
        assert _click_icon_button(view, ft.Icons.DELETE_OUTLINE, occurrence=idx), "icône suppression utilisateur introuvable"
        _click_last_dialog_action(page)
        remaining = ctx.users.list()
        assert not any(x["id"] == u["id"] for x in remaining), "la suppression utilisateur n'a pas été persistée"

    check("Édition + suppression : Utilisateur", test_user_edit_delete)

    # ─── MTN MoMo : échec propre attendu si le réseau/les identifiants ne
    #     permettent pas d'aboutir dans cet environnement (aucune exception
    #     Python ne doit fuiter jusqu'à l'UI, quelle que soit la cause) ────
    def test_momo_graceful_failure():
        s = ctx.cemetery.create_section({"nom": "Section MoMo Test", "description": None, "superficie": None})
        b = ctx.cemetery.create_bloc({"section_id": s["id"], "nom": "Bloc MoMo Test"})
        g = ctx.cemetery.create_grave({"bloc_id": b["id"], "numero": "MOMO-001", "status": "libre"})
        c = ctx.concessions.create({"grave_id": g["id"], "famille_nom": "Famille MoMo", "duree": "10_ans", "date_debut": "2026-01-01", "montant_total": 50000})
        view = build_paiements_view(page, ctx)
        assert _click_text_button(view, "MTN MoMo") or _click_new_button(page, view, "MTN MoMo"), "bouton MTN MoMo introuvable"
        assert page.dialog is not None, "le dialogue MoMo ne s'est pas ouvert"
        # Doit échouer proprement (ApiError catchée en interne -> snackbar), sans exception non gérée
        _fill_and_submit_dialog(page, "momo initiate")  # ne doit pas lever d'exception
        ctx.concessions.delete(c["id"])
        ctx.cemetery.delete_grave(g["id"])
        ctx.cemetery.delete_bloc(b["id"])
        ctx.cemetery.delete_section(s["id"])

    check("MTN MoMo : échec propre (réseau/identifiants indisponibles ici)", test_momo_graceful_failure)


def run_responsive_tests(page, ctx, fails):
    """Vérifie le comportement responsive : bascule mobile/desktop, présence
    du tiroir de navigation (drawer) en mode mobile, ouverture via l'icône
    hamburger, et fermeture + navigation au clic sur un lien du tiroir."""
    from app.pages.dashboard_page import build_dashboard_view
    from app.components.layout import is_mobile

    def check(name, fn):
        try:
            fn()
            print(f"[OK ] {name}")
        except Exception as e:
            print(f"[FAIL] {name} -> {type(e).__name__}: {e}")
            traceback.print_exc()
            fails.append(name)

    def test_desktop_no_drawer():
        page.width = 1200
        assert not is_mobile(page), "1200px ne devrait pas être détecté comme mobile"
        view = build_dashboard_view(page, ctx)
        assert view.drawer is None, "Aucun drawer ne devrait être présent en mode desktop"

    def test_mobile_has_drawer_and_hamburger():
        page.width = 375
        assert is_mobile(page), "375px devrait être détecté comme mobile"
        view = build_dashboard_view(page, ctx)
        assert view.drawer is not None, "Un drawer devrait être présent en mode mobile"

        hamburger = next((c for c in _walk_controls(view) if getattr(c, "icon", None) == ft.Icons.MENU), None)
        assert hamburger is not None, "L'icône hamburger devrait être présente en mode mobile"

        page.show_drawer_calls = 0
        # Le handler du hamburger est `async def open_drawer(e): await page.show_drawer()`.
        # Flet exécute nativement les handlers async ; ici on le fait manuellement.
        asyncio.run(hamburger.on_click(FakeEvent()))
        assert page.show_drawer_calls == 1, "Le clic sur le hamburger devrait appeler page.show_drawer() exactement une fois"

    def test_mobile_drawer_navigation_closes_and_navigates():
        page.width = 375
        page.route = "/dashboard"
        view = build_dashboard_view(page, ctx)
        drawer = view.drawer
        assert drawer is not None

        # Cherche un item de navigation vers /sections dans le contenu du drawer
        nav_item = None
        for ctrl in _walk_controls(drawer):
            if isinstance(ctrl, ft.Container) and getattr(ctrl, "on_click", None):
                # Les items de nav sont des Container avec on_click sync (sync_navigate)
                nav_item = ctrl
                break
        assert nav_item is not None, "Aucun item de navigation trouvé dans le drawer"

        page.close_drawer_calls = 0
        nav_item.on_click(FakeEvent())
        assert page.close_drawer_calls >= 1, "La navigation depuis le drawer devrait fermer le drawer (page.close_drawer)"

    check("Responsive : pas de drawer en mode desktop (1200px)", test_desktop_no_drawer)
    check("Responsive : drawer + hamburger présents en mode mobile (375px)", test_mobile_has_drawer_and_hamburger)
    check("Responsive : navigation depuis le drawer ferme le tiroir", test_mobile_drawer_navigation_closes_and_navigates)

    page.width = 1200  # remet le mode desktop par défaut pour la suite des tests


def run_input_robustness_tests(page, ctx, fails):
    """Non-régression du bug rapporté : saisir '3 800' (espace comme
    séparateur de milliers) dans un champ numérique faisait planter
    l'application avec une ValueError non gérée. Vérifie que ce type de
    saisie est maintenant accepté (ou refusé proprement, jamais un crash)
    sur tous les champs numériques concernés."""
    from app.pages.sections_page import build_sections_view
    from app.pages.concessions_page import build_concessions_view
    from app.pages.graves_page import build_graves_view

    def check(name, fn):
        try:
            fn()
            print(f"[OK ] {name}")
        except Exception as e:
            print(f"[FAIL] {name} -> {type(e).__name__}: {e}")
            traceback.print_exc()
            fails.append(name)

    def set_field_by_label(dialog, label_substring, value):
        for ctrl in _walk_controls(dialog.content):
            if isinstance(ctrl, ft.TextField) and label_substring.lower() in (ctrl.label or "").lower():
                ctrl.value = value
                return True
        return False

    def test_section_superficie_with_space():
        page.dialog = None
        view = build_sections_view(page, ctx)
        assert _click_new_button(page, view, "Nouvelle section"), "bouton introuvable"
        dialog = page.dialog
        set_field_by_label(dialog, "nom de la section", "Section Robustesse Espace")
        set_field_by_label(dialog, "superficie", "3 800")  # <- exactement le cas signalé
        dialog.actions[-1].on_click(FakeEvent())
        assert not dialog.open, "le formulaire aurait dû accepter '3 800' et se fermer sans planter"
        sections = ctx.cemetery.list_sections()
        match = next((s for s in sections if s["nom"] == "Section Robustesse Espace"), None)
        assert match is not None and match["superficie"] == 3800.0, f"superficie mal interprétée : {match}"
        ctx.cemetery.delete_section(match["id"])

    def test_section_superficie_invalid_text():
        page.dialog = None
        view = build_sections_view(page, ctx)
        assert _click_new_button(page, view, "Nouvelle section"), "bouton introuvable"
        dialog = page.dialog
        set_field_by_label(dialog, "nom de la section", "Section Robustesse Invalide")
        set_field_by_label(dialog, "superficie", "abc")
        dialog.actions[-1].on_click(FakeEvent())
        assert dialog.open, "un texte non numérique doit être refusé (dialogue reste ouvert), pas planter"
        sections = ctx.cemetery.list_sections()
        assert not any(s["nom"] == "Section Robustesse Invalide" for s in sections), "la section n'aurait pas dû être créée"

    def test_concession_montant_with_space_and_comma():
        s = ctx.cemetery.create_section({"nom": "Section Robustesse Concession", "description": None, "superficie": None})
        b = ctx.cemetery.create_bloc({"section_id": s["id"], "nom": "Bloc Robustesse"})
        g = ctx.cemetery.create_grave({"bloc_id": b["id"], "numero": "ROB-001", "status": "libre"})

        page.dialog = None
        view = build_concessions_view(page, ctx)
        assert _click_new_button(page, view, "Nouvelle concession"), "bouton introuvable"
        dialog = page.dialog
        set_field_by_label(dialog, "nom de la famille", "Famille Robustesse")
        set_field_by_label(dialog, "date de début", "2026-01-01")
        set_field_by_label(dialog, "montant total", "250 000,50")  # espace + virgule décimale
        dialog.actions[-1].on_click(FakeEvent())
        assert not dialog.open, "le formulaire aurait dû accepter '250 000,50' et se fermer sans planter"

        concessions = ctx.concessions.list()
        match = next((c for c in concessions if c["famille_nom"] == "Famille Robustesse"), None)
        assert match is not None and abs(match["montant_total"] - 250000.50) < 0.01, f"montant mal interprété : {match}"
        ctx.concessions.delete(match["id"])
        ctx.cemetery.delete_grave(g["id"])
        ctx.cemetery.delete_bloc(b["id"])
        ctx.cemetery.delete_section(s["id"])

    def test_grave_latitude_out_of_range():
        s = ctx.cemetery.create_section({"nom": "Section Robustesse Lat", "description": None, "superficie": None})
        b = ctx.cemetery.create_bloc({"section_id": s["id"], "nom": "Bloc Robustesse Lat"})

        page.dialog = None
        view = build_graves_view(page, ctx)
        assert _click_new_button(page, view, "Nouveau caveau"), "bouton introuvable"
        dialog = page.dialog
        set_field_by_label(dialog, "numéro du caveau", "ROB-LAT-001")
        set_field_by_label(dialog, "latitude", "500")  # hors bornes (-90..90)
        dialog.actions[-1].on_click(FakeEvent())
        assert dialog.open, "une latitude hors bornes (-90..90) doit être refusée, pas planter"

        ctx.cemetery.delete_bloc(b["id"])
        ctx.cemetery.delete_section(s["id"])

    check("Robustesse : superficie avec espace '3 800' (bug rapporté)", test_section_superficie_with_space)
    check("Robustesse : superficie avec texte invalide -> refus propre", test_section_superficie_invalid_text)
    check("Robustesse : montant avec espace + virgule '250 000,50'", test_concession_montant_with_space_and_comma)
    check("Robustesse : latitude hors bornes -> refus propre", test_grave_latitude_out_of_range)


def run_form_submission_tests(page, ctx, fails):
    """Exerce le chemin complet Bouton -> Dialogue -> Remplissage -> Sauvegarde
    -> Fermeture pour chaque module CRUD, contre le backend réel."""
    from app.pages.sections_page import build_sections_view
    from app.pages.blocs_page import build_blocs_view
    from app.pages.graves_page import build_graves_view
    from app.pages.reservations_page import build_reservations_view
    from app.pages.concessions_page import build_concessions_view
    from app.pages.paiements_page import build_paiements_view
    from app.pages.exhumations_page import build_exhumations_view
    from app.pages.users_page import build_users_view

    def check_form(name, view_builder, button_hint):
        page.dialog = None
        try:
            view = view_builder(page, ctx)
            clicked = _click_new_button(page, view, button_hint)
            if not clicked:
                print(f"[FAIL] {name} -> bouton '{button_hint}' introuvable ou sans données prérequises")
                fails.append(name)
                return
            ok = _fill_and_submit_dialog(page, name)
            if ok:
                print(f"[OK ] {name} (formulaire rempli + soumis + créé en base)")
            else:
                print(f"[FAIL] {name} -> le dialogue ne s'est pas fermé (échec de sauvegarde)")
                fails.append(name)
        except Exception as e:
            print(f"[FAIL] {name} -> {type(e).__name__}: {e}")
            traceback.print_exc()
            fails.append(name)

    # Sections d'abord (prérequis pour blocs -> caveaux -> reste de la chaîne)
    check_form("Formulaire: Nouvelle section", build_sections_view, "Nouvelle section")
    check_form("Formulaire: Nouveau bloc", build_blocs_view, "Nouveau bloc")
    check_form("Formulaire: Nouveau caveau", build_graves_view, "Nouveau caveau")
    check_form("Formulaire: Nouvelle réservation", build_reservations_view, "Nouvelle réservation")
    check_form("Formulaire: Nouvelle concession", build_concessions_view, "Nouvelle concession")
    check_form("Formulaire: Nouveau paiement", build_paiements_view, "Nouveau paiement")

    # Le formulaire d'exhumation exige un caveau au statut "occupe" : aucun des
    # tests précédents n'en crée un via l'UI (les caveaux créés restent
    # "libre"). On en prépare un directement via l'API pour ne pas fausser
    # le test avec un prérequis métier non lié au formulaire lui-même.
    try:
        s = ctx.cemetery.create_section({"nom": "Section Exhum Test", "description": None, "superficie": None})
        b = ctx.cemetery.create_bloc({"section_id": s["id"], "nom": "Bloc Exhum Test"})
        g = ctx.cemetery.create_grave({"bloc_id": b["id"], "numero": "EXHUM-001", "status": "libre"})
        ctx.cemetery.create_defunt({"nom": "Test", "prenom": "Exhumation", "date_deces": "2026-01-01", "grave_id": g["id"]})
        print("[OK ] Préparation d'un caveau occupé pour le test du formulaire d'exhumation")
    except ApiError as e:
        print(f"[FAIL] Préparation caveau occupé -> {e.message}")
        fails.append("préparation caveau occupé (exhumation)")

    check_form("Formulaire: Planifier exhumation", build_exhumations_view, "Planifier une exhumation")
    check_form("Formulaire: Nouvel utilisateur", build_users_view, "Nouvel utilisateur")


def run():
    from app.pages.dashboard_page import build_dashboard_view
    from app.pages.map_page import build_map_view
    from app.pages.sections_page import build_sections_view
    from app.pages.blocs_page import build_blocs_view
    from app.pages.graves_page import build_graves_view
    from app.pages.reservations_page import build_reservations_view
    from app.pages.concessions_page import build_concessions_view
    from app.pages.paiements_page import build_paiements_view
    from app.pages.exhumations_page import build_exhumations_view
    from app.pages.analytics_page import build_analytics_view
    from app.pages.users_page import build_users_view
    from app.pages.audit_page import build_audit_view
    from app.pages.login_page import build_login_view
    from app.pages.public_search_page import build_public_search_view

    page = FakePage()
    ctx = SessionContext()

    fails = []

    def check(name, fn):
        try:
            fn()
            print(f"[OK ] {name}")
        except Exception as e:
            print(f"[FAIL] {name} -> {type(e).__name__}: {e}")
            traceback.print_exc()
            fails.append(name)

    # Pages publiques (sans authentification)
    check("login_page (construction)", lambda: build_login_view(page, ctx))
    check("public_search_page (construction)", lambda: build_public_search_view(page, ctx))

    # Authentification (admin)
    profile = ctx.auth.login("admin@cimetiere.cg", "AdminTest123!")
    ctx.set_profile(profile)
    print(f"[OK ] login réussi, rôle = {ctx.role}")

    # Préparer un minimum de données pour que les pages CRUD affichent quelque chose
    try:
        section = ctx.cemetery.create_section({"nom": "Section Frontend Test", "description": "test", "superficie": 100})
        bloc = ctx.cemetery.create_bloc({"section_id": section["id"], "nom": "Bloc FT1"})
        grave = ctx.cemetery.create_grave({"bloc_id": bloc["id"], "numero": "FT-001", "status": "libre", "latitude": -4.79, "longitude": 11.86})
        print("[OK ] Données de test créées (section/bloc/caveau)")
    except ApiError as e:
        print(f"[FAIL] Préparation des données -> {e.message}")
        fails.append("préparation données")

    # Pages protégées (rôle admin = accès total)
    check("dashboard_page", lambda: build_dashboard_view(page, ctx))
    check("map_page", lambda: build_map_view(page, ctx))
    check("sections_page", lambda: build_sections_view(page, ctx))
    check("blocs_page", lambda: build_blocs_view(page, ctx))
    check("graves_page", lambda: build_graves_view(page, ctx))
    check("reservations_page", lambda: build_reservations_view(page, ctx))
    check("concessions_page", lambda: build_concessions_view(page, ctx))
    check("paiements_page", lambda: build_paiements_view(page, ctx))
    check("exhumations_page", lambda: build_exhumations_view(page, ctx))
    check("analytics_page", lambda: build_analytics_view(page, ctx))
    check("users_page", lambda: build_users_view(page, ctx))
    check("audit_page", lambda: build_audit_view(page, ctx))

    # ─── Simulation complète : clic bouton -> remplissage -> soumission ───
    print("\n--- Tests de robustesse des saisies numériques (non-régression) ---")
    run_input_robustness_tests(page, ctx, fails)

    print("\n--- Tests de soumission de formulaires (câblage UI -> API) ---")
    run_form_submission_tests(page, ctx, fails)

    print("\n--- Tests d'édition / suppression / transitions de statut ---")
    run_edit_delete_status_tests(page, ctx, fails)

    print("\n--- Tests de responsivité (mobile/desktop, drawer, hamburger) ---")
    run_responsive_tests(page, ctx, fails)

    # Nettoyage des données de base (les données créées par les tests de
    # soumission de formulaires restent en base : ce script est destiné à une
    # base de test jetable, pas à un environnement de production).
    try:
        ctx.cemetery.delete_grave(grave["id"])
        ctx.cemetery.delete_bloc(bloc["id"])
        ctx.cemetery.delete_section(section["id"])
        print("[OK ] Nettoyage des données de test")
    except Exception:
        pass

    # ─── Composants de formulaire (utilisés dans tous les dialogues CRUD) ──
    from app.components.theme import text_field, dropdown_field, show_snackbar, confirm_dialog
    from app.components.data_table import form_dialog

    check("text_field (simple)", lambda: text_field("Champ test", width=300))
    check("text_field (multiline)", lambda: text_field("Champ test", width=300, multiline=True, min_lines=2))
    check("text_field (password)", lambda: text_field("Mot de passe", password=True, can_reveal_password=True, width=300))
    check("dropdown_field (tuples)", lambda: dropdown_field("Choix", [("a", "Option A"), ("b", "Option B")], value="a", width=300))
    check("show_snackbar", lambda: show_snackbar(page, "Message de test", success=True))
    check("show_snackbar (erreur)", lambda: show_snackbar(page, "Message d'erreur", success=False))
    check("confirm_dialog", lambda: confirm_dialog(page, "Titre", "Message de confirmation", lambda: None))
    check("form_dialog", lambda: form_dialog(page, "Titre formulaire", [text_field("Champ 1", width=300), dropdown_field("Champ 2", [("x", "X")], width=300)], lambda close: None))

    print("\n" + "=" * 60)
    if fails:
        print(f"ÉCHECS ({len(fails)}): {fails}")
        sys.exit(1)
    print("TOUTES LES PAGES SE CONSTRUISENT SANS ERREUR ✅")
    sys.exit(0)


if __name__ == "__main__":
    run()
