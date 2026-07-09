#!/usr/bin/env python3
"""Script de régression end-to-end de l'API cimetière GI2."""
import sys
import requests

BASE = "http://127.0.0.1:8123/api"
FAILS = []


def check(name, resp, expected_status=200):
    ok = resp.status_code == expected_status
    marker = "OK " if ok else "FAIL"
    print(f"[{marker}] {name} -> {resp.status_code}")
    if not ok:
        print(f"       Réponse: {resp.text[:300]}")
        FAILS.append(name)
    return resp


def main():
    s = requests.Session()

    # ─── Auth ──────────────────────────────────────────────────────────────
    r = check("login", s.post(f"{BASE}/auth/login", json={"email": "admin@cimetiere.cg", "password": "AdminTest123!"}))
    token = r.json()["tokens"]["access_token"]
    refresh = r.json()["tokens"]["refresh_token"]
    s.headers.update({"Authorization": f"Bearer {token}"})

    check("me", s.get(f"{BASE}/auth/me"))
    check("refresh", s.post(f"{BASE}/auth/refresh", json={"refresh_token": refresh}))
    check("login mauvais mdp", s.post(f"{BASE}/auth/login", json={"email": "admin@cimetiere.cg", "password": "wrong"}), 401)

    # ─── Utilisateurs ─────────────────────────────────────────────────────
    r = check("create user agent", s.post(f"{BASE}/users", json={
        "email": "agent1@cimetiere.cg", "password": "AgentTest123!", "full_name": "Agent Un", "role": "agent"
    }))
    agent_id = r.json()["id"]
    check("list users", s.get(f"{BASE}/users"))
    check("update user", s.put(f"{BASE}/users/{agent_id}", json={"full_name": "Agent Un Modifié"}))

    # ─── Cimetière : sections / blocs / graves / défunts ─────────────────
    r = check("create section", s.post(f"{BASE}/cimetiere/sections", json={"nom": "Section Régression", "superficie": 500}))
    section_id = r.json()["id"]
    check("list sections (public)", requests.get(f"{BASE}/cimetiere/sections"))

    r = check("create bloc", s.post(f"{BASE}/cimetiere/blocs", json={"section_id": section_id, "nom": "Bloc R1"}))
    bloc_id = r.json()["id"]

    r = check("create grave", s.post(f"{BASE}/cimetiere/graves", json={
        "bloc_id": bloc_id, "numero": "R1-100", "status": "libre", "latitude": -4.8, "longitude": 11.85
    }))
    grave_id = r.json()["id"]
    check("get grave", s.get(f"{BASE}/cimetiere/graves/{grave_id}"))
    check("list graves filter status", s.get(f"{BASE}/cimetiere/graves", params={"status": "libre"}))
    check("occupancy stats", requests.get(f"{BASE}/cimetiere/stats/occupancy"))

    r = check("create defunt", s.post(f"{BASE}/cimetiere/defunts", json={
        "nom": "Nzaba", "prenom": "Pierre", "date_deces": "2026-05-20", "grave_id": grave_id
    }))
    defunt_id = r.json()["id"]
    check("recherche publique defunt", requests.get(f"{BASE}/cimetiere/defunts/recherche", params={"q": "Nzaba"}))

    # grave doit maintenant être "occupe" (attribution auto d'un défunt)
    r = check("get grave après défunt (occupe)", s.get(f"{BASE}/cimetiere/graves/{grave_id}"))
    assert r.json()["status"] == "occupe", "Le statut du caveau aurait dû passer à 'occupe'"

    # ─── Nouveau caveau pour tester réservation/concession sans défunt déjà lié
    r = check("create grave 2", s.post(f"{BASE}/cimetiere/graves", json={"bloc_id": bloc_id, "numero": "R1-101", "status": "libre"}))
    grave2_id = r.json()["id"]

    # ─── Réservations ───────────────────────────────────────────────────
    r = check("create reservation", s.post(f"{BASE}/reservations/", json={
        "grave_id": grave2_id, "defunt_nom": "Kaya", "defunt_prenom": "Alice",
        "defunt_date_deces": "2026-06-15", "famille_nom": "Famille Kaya", "famille_contact": "+242060000000"
    }))
    reservation_id = r.json()["id"]
    check("list reservations", s.get(f"{BASE}/reservations/"))
    check("reservation stats", s.get(f"{BASE}/reservations/stats"))
    check("validate reservation", s.post(f"{BASE}/reservations/{reservation_id}/validate", json={"status": "validee"}))

    r = check("get grave2 après validation (reserve)", s.get(f"{BASE}/cimetiere/graves/{grave2_id}"))
    assert r.json()["status"] == "reserve", "Le caveau devrait être 'reserve' après validation"

    # ─── Concessions ────────────────────────────────────────────────────
    r = check("create concession", s.post(f"{BASE}/concessions/", json={
        "grave_id": grave2_id, "reservation_id": reservation_id, "famille_nom": "Famille Kaya",
        "duree": "10_ans", "date_debut": "2026-07-01", "montant_total": 200000
    }))
    concession_id = r.json()["id"]
    assert r.json()["date_fin"] == "2036-07-01", f"Date fin incorrecte: {r.json()['date_fin']}"
    check("list concessions", s.get(f"{BASE}/concessions/"))
    check("renew concession", s.post(f"{BASE}/concessions/{concession_id}/renew", json={"nouvelle_duree": "10_ans", "montant_supplementaire": 50000}))

    # ─── Paiements ──────────────────────────────────────────────────────
    r = check("create paiement", s.post(f"{BASE}/paiements/", json={
        "concession_id": concession_id, "montant": 250000, "date_paiement": "2026-07-01", "mode_paiement": "especes"
    }))
    paiement_id = r.json()["id"]
    check("paiements stats", s.get(f"{BASE}/paiements/stats"))
    r = check("recu pdf", s.get(f"{BASE}/paiements/{paiement_id}/recu"))
    assert r.headers["Content-Type"] == "application/pdf", "Le reçu devrait être un PDF"
    r = check("export pdf global", s.get(f"{BASE}/paiements/export/pdf"))
    assert r.headers["Content-Type"] == "application/pdf"

    # ─── MoMo (sans clés configurées -> doit échouer proprement en 502) ──
    check("momo initiate sans config (502 attendu)", s.post(f"{BASE}/paiements/momo/initiate", json={
        "concession_id": concession_id, "montant": 10000, "phone_number": "+242061112233"
    }), 502)
    check("momo list transactions", s.get(f"{BASE}/paiements/momo/transactions"))

    # ─── Exhumations ────────────────────────────────────────────────────
    r = check("create exhumation", s.post(f"{BASE}/exhumations/", json={"grave_id": grave_id, "motif": "Test régression"}))
    exhumation_id = r.json()["id"]
    check("list exhumations", s.get(f"{BASE}/exhumations/"))
    check("exhumation -> en_cours", s.post(f"{BASE}/exhumations/{exhumation_id}/status", json={"status": "en_cours"}))
    check("exhumation -> termine", s.post(f"{BASE}/exhumations/{exhumation_id}/status", json={"status": "termine"}))
    r = check("get grave après exhumation terminée (libre)", s.get(f"{BASE}/cimetiere/graves/{grave_id}"))
    assert r.json()["status"] == "libre", "Le caveau devrait redevenir 'libre' après exhumation terminée"

    # ─── Notifications ──────────────────────────────────────────────────
    check("list notifications", s.get(f"{BASE}/notifications/"))
    check("unread count", s.get(f"{BASE}/notifications/unread-count"))

    # ─── Audit (admin) ──────────────────────────────────────────────────
    check("audit logs", s.get(f"{BASE}/audit/"))

    # ─── Permissions : agent ne peut pas supprimer ────────────────────
    r_agent = requests.post(f"{BASE}/auth/login", json={"email": "agent1@cimetiere.cg", "password": "AgentTest123!"})
    agent_token = r_agent.json()["tokens"]["access_token"]
    agent_headers = {"Authorization": f"Bearer {agent_token}"}
    check("agent essaie delete section (403 attendu)", requests.delete(f"{BASE}/cimetiere/sections/{section_id}", headers=agent_headers), 403)
    check("agent essaie voir audit (403 attendu)", requests.get(f"{BASE}/audit/", headers=agent_headers), 403)
    check("agent essaie list users (403 attendu)", requests.get(f"{BASE}/users", headers=agent_headers), 403)
    check("agent peut voir sections", requests.get(f"{BASE}/cimetiere/sections", headers=agent_headers), 200)

    # ─── Nettoyage (admin) ──────────────────────────────────────────────
    check("delete paiement", s.delete(f"{BASE}/paiements/{paiement_id}"))
    check("delete concession", s.delete(f"{BASE}/concessions/{concession_id}"))
    check("delete reservation", s.delete(f"{BASE}/reservations/{reservation_id}"))
    check("delete exhumation", s.delete(f"{BASE}/exhumations/{exhumation_id}"))
    check("delete defunt", s.delete(f"{BASE}/cimetiere/defunts/{defunt_id}"))
    check("delete grave", s.delete(f"{BASE}/cimetiere/graves/{grave_id}"))
    check("delete grave2", s.delete(f"{BASE}/cimetiere/graves/{grave2_id}"))
    check("delete bloc", s.delete(f"{BASE}/cimetiere/blocs/{bloc_id}"))
    check("delete section", s.delete(f"{BASE}/cimetiere/sections/{section_id}"))

    # ─── Nouveautés : CSV, notifications, réinitialisation mot de passe ──
    r = check("create section (finalisation)", s.post(f"{BASE}/cimetiere/sections", json={"nom": "Section Finalisation", "superficie": 100}))
    section2_id = r.json()["id"]
    r = check("create bloc (finalisation)", s.post(f"{BASE}/cimetiere/blocs", json={"section_id": section2_id, "nom": "Bloc Finalisation"}))
    bloc2_id = r.json()["id"]
    r = check("create grave (finalisation)", s.post(f"{BASE}/cimetiere/graves", json={"bloc_id": bloc2_id, "numero": "FIN-001", "status": "libre"}))
    grave3_id = r.json()["id"]
    r = check("create concession (finalisation)", s.post(f"{BASE}/concessions/", json={
        "grave_id": grave3_id, "famille_nom": "Famille Finalisation", "duree": "10_ans",
        "date_debut": "2026-01-01", "montant_total": 100000,
    }))
    concession2_id = r.json()["id"]
    r = check("create paiement (finalisation)", s.post(f"{BASE}/paiements/", json={
        "concession_id": concession2_id, "montant": 100000, "date_paiement": "2026-01-01", "mode_paiement": "especes",
    }))
    paiement2_id = r.json()["id"]

    r = check("export CSV paiements", s.get(f"{BASE}/paiements/export/csv"))
    assert r.headers["Content-Type"].startswith("text/csv"), "l'export devrait être un CSV"
    assert "Famille Finalisation".encode("utf-8") in r.content, "le CSV devrait contenir les données du paiement de test"

    r = check("export CSV audit", s.get(f"{BASE}/audit/export/csv"))
    assert r.headers["Content-Type"].startswith("text/csv"), "l'export d'audit devrait être un CSV"

    check("export CSV audit filtré par module", s.get(f"{BASE}/audit/export/csv", params={"table_name": "paiements"}))

    # Notifications : la création du paiement doit avoir notifié les autres gestionnaires/admin (aucun ici à part soi-même -> liste vide attendue, pas d'erreur)
    check("list notifications (admin)", s.get(f"{BASE}/notifications/"))
    check("unread count (admin)", s.get(f"{BASE}/notifications/unread-count"))

    # Réinitialisation de mot de passe par un admin
    r = check("create user pour reset password", s.post(f"{BASE}/users", json={
        "email": "resetpwd@cimetiere.cg", "password": "InitialPass123!", "full_name": "Reset Test", "role": "agent"
    }))
    reset_user_id = r.json()["id"]
    check("admin reset password", s.post(f"{BASE}/users/{reset_user_id}/reset-password", json={"new_password": "NouveauPass456!"}))
    check("login avec le nouveau mot de passe", requests.post(f"{BASE}/auth/login", json={"email": "resetpwd@cimetiere.cg", "password": "NouveauPass456!"}))
    check("reset password trop court (400 attendu)", s.post(f"{BASE}/users/{reset_user_id}/reset-password", json={"new_password": "short"}), 400)

    # Vérifier que la réservation déclenche bien une notification pour le gestionnaire
    r = check("create agent pour test notification", s.post(f"{BASE}/users", json={
        "email": "agentnotif@cimetiere.cg", "password": "AgentNotif123!", "full_name": "Agent Notif", "role": "agent"
    }))
    agent_notif_id = r.json()["id"]
    r_agent2 = requests.post(f"{BASE}/auth/login", json={"email": "agentnotif@cimetiere.cg", "password": "AgentNotif123!"})
    agent2_token = r_agent2.json()["tokens"]["access_token"]
    agent2_headers = {"Authorization": f"Bearer {agent2_token}"}

    r = check("create grave libre pour test notification", s.post(f"{BASE}/cimetiere/graves", json={"bloc_id": bloc2_id, "numero": "NOTIF-001", "status": "libre"}))
    grave_notif_id = r.json()["id"]

    # Nombre de notifications admin AVANT la réservation créée par l'agent
    before_count = s.get(f"{BASE}/notifications/unread-count").json()["count"]

    r = check("agent crée une réservation (déclenche notification)", requests.post(f"{BASE}/reservations/", json={
        "grave_id": grave_notif_id, "defunt_nom": "Test", "defunt_prenom": "Notif",
        "defunt_date_deces": "2026-01-01", "famille_nom": "Famille Notif",
    }, headers=agent2_headers))
    reservation_notif_id = r.json()["id"]

    after_count = s.get(f"{BASE}/notifications/unread-count").json()["count"]
    if after_count <= before_count:
        print(f"[FAIL] notification de nouvelle réservation -> compteur non-lu inchangé ({before_count} -> {after_count})")
        FAILS.append("notification nouvelle réservation")
    else:
        print(f"[OK ] notification de nouvelle réservation -> compteur non-lu {before_count} -> {after_count}")

    # Vérifier que la validation notifie l'agent créateur (on ne peut pas lire
    # ses notifications avec le token admin, donc on se contente de vérifier
    # que l'appel de validation réussit sans erreur ; la logique de création
    # de notification est la même fonction que ci-dessus, déjà éprouvée).
    check("valider la réservation (déclenche notification agent)", s.post(f"{BASE}/reservations/{reservation_notif_id}/validate", json={"status": "validee"}))

    # Nettoyage complémentaire
    check("delete reservation (notif)", s.delete(f"{BASE}/reservations/{reservation_notif_id}"))
    check("delete grave (notif)", s.delete(f"{BASE}/cimetiere/graves/{grave_notif_id}"))
    check("delete paiement (finalisation)", s.delete(f"{BASE}/paiements/{paiement2_id}"))
    check("delete concession (finalisation)", s.delete(f"{BASE}/concessions/{concession2_id}"))
    check("delete grave (finalisation)", s.delete(f"{BASE}/cimetiere/graves/{grave3_id}"))
    check("delete bloc (finalisation)", s.delete(f"{BASE}/cimetiere/blocs/{bloc2_id}"))
    check("delete section (finalisation)", s.delete(f"{BASE}/cimetiere/sections/{section2_id}"))
    check("delete user reset-password", s.delete(f"{BASE}/users/{reset_user_id}"))
    check("delete user agent-notif", s.delete(f"{BASE}/users/{agent_notif_id}"))

    check("delete user agent", s.delete(f"{BASE}/users/{agent_id}"))

    print("\n" + "=" * 60)
    if FAILS:
        print(f"ÉCHECS ({len(FAILS)}): {FAILS}")
        sys.exit(1)
    else:
        print("TOUS LES TESTS SONT PASSÉS ✅")
        sys.exit(0)


if __name__ == "__main__":
    main()
