# Démarrage rapide — Gestion de Cimetière GI2 2026 v2

> 💻 Vous êtes sous **Windows** : utilisez les commandes de la section
> [Windows](#windows) ci-dessous. Les scripts `.sh` (Linux/macOS) sont aussi
> fournis à titre de référence dans `scripts_install/`.

## Versions exactes utilisées

| Composant | Version | Statut |
|---|---|---|
| **Flet** | `0.85.3` | ✅ Dernière version stable disponible sur PyPI |
| **flet-web** | `0.85.3` | ✅ Requis pour le mode web (voir note ci-dessous) |
| **flet-webview** | `0.85.3` | ✅ Utilisé pour la carte Google Maps intégrée |
| **httpx** | `0.28.1` | ✅ Dernière version stable |
| **python-decouple** | `3.8` | ✅ Dernière version stable |
| **Django** | `5.2.15` | ✅ Version LTS (support long terme, la plus stable disponible) |
| **django-ninja** | `1.6.2` | ✅ Dernière version stable |
| **PostgreSQL** | 14+ | À installer séparément |

Toutes ces versions ont été vérifiées empiriquement (régression complète de
65+ scénarios API + 30+ parcours frontend) — voir `scripts_install/run_tests.bat`
pour rejouer cette vérification sur votre machine.

---

## Windows

### Prérequis
- **Python 3.11+** installé avec l'option *"Add python.exe to PATH"* cochée
  lors de l'installation (https://www.python.org/downloads/)
- **PostgreSQL 14+** installé (https://www.postgresql.org/download/windows/)

### Si vous n'avez PAS ENCORE installé le projet

Ouvrez une **invite de commandes** (`cmd.exe`) à la racine du projet
(`cimetiere_gi2\`) et lancez :

```bat
scripts_install\setup.bat
```

Ce script va, dans l'ordre :
1. Vérifier Python et PostgreSQL
2. Créer les environnements virtuels backend et frontend (`backend\venv`, `frontend\venv`)
3. Installer toutes les dépendances (versions ci-dessus)
4. Créer `backend\.env` et `frontend\.env` s'ils n'existent pas déjà
   *(dans cette livraison, `backend\.env` est déjà pré-rempli avec votre clé
   Google Maps et vos identifiants MTN MoMo — il ne vous reste qu'à
   compléter `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`)*
5. **S'arrêter pour vous laisser éditer `backend\.env`** si besoin
6. Relancez `scripts_install\setup.bat` : il détecte que `.env` existe déjà et continue
7. Applique les migrations de base de données
8. Vous demande interactivement de créer votre premier compte administrateur

> ⚠️ Le mot de passe saisi à l'étape 8 s'affiche en clair dans la fenêtre
> (limitation de l'invite de commandes standard). Assurez-vous que personne
> ne regarde votre écran à ce moment, ou changez le mot de passe une fois
> connecté à l'application.

Si l'étape des migrations échoue, c'est presque toujours un problème de
connexion à PostgreSQL (vérifiez `DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD`, et que le service PostgreSQL est bien démarré — visible dans
*Services* Windows sous le nom `postgresql-x64-...`).

### Si vous avez DÉJÀ installé le projet (lancement quotidien)

Deux invites de commandes séparées :

```bat
REM Fenêtre 1
scripts_install\start_backend.bat

REM Fenêtre 2
scripts_install\start_frontend.bat
```

Puis ouvrez votre navigateur sur : **http://localhost:8550**

- Le backend écoute sur `http://localhost:8000` (API sur `/api`, admin Django sur `/admin`)
- Le frontend écoute sur `http://localhost:8550`

Arrêt : `Ctrl+C` dans chaque fenêtre, ou fermez simplement les fenêtres.

### Vérifier que tout fonctionne (optionnel)

```bat
scripts_install\run_tests.bat
```

Une sortie `TOUS LES TESTS SONT PASSES` confirme une installation saine.

### Problèmes fréquents sous Windows

| Symptôme | Cause probable | Solution |
|---|---|---|
| `'python' n'est pas reconnu...` | Python non ajouté au PATH | Réinstallez Python en cochant "Add Python to PATH", ou utilisez `py` à la place de `python` dans les scripts |
| Le script se ferme instantanément sans message | Erreur silencieuse | Lancez-le depuis une invite de commandes déjà ouverte (pas en double-clic) pour voir les messages d'erreur |
| `psql` introuvable mais PostgreSQL est installé | PostgreSQL non ajouté au PATH | Ajoutez `C:\Program Files\PostgreSQL\<version>\bin` à votre variable d'environnement PATH, ou ignorez cet avertissement si vous gérez PostgreSQL autrement (pgAdmin, service distant) |
| `connection to server ... Connection refused` | Le service PostgreSQL n'est pas démarré | Ouvrez *Services* (services.msc), cherchez `postgresql-x64-...`, démarrez-le |

---

## macOS / Linux

```bash
chmod +x scripts_install/*.sh
./scripts_install/setup.sh
```

Puis pour le lancement quotidien :

```bash
# Terminal 1
./scripts_install/start_backend.sh

# Terminal 2
./scripts_install/start_frontend.sh
```

Vérification : `./scripts_install/run_tests.sh`

---

## Récapitulatif des scripts

| Rôle | Windows | macOS / Linux |
|---|---|---|
| Installation complète | `scripts_install\setup.bat` | `scripts_install/setup.sh` |
| Démarrer le backend | `scripts_install\start_backend.bat` | `scripts_install/start_backend.sh` |
| Démarrer le frontend | `scripts_install\start_frontend.bat` | `scripts_install/start_frontend.sh` |
| Vérifier l'installation | `scripts_install\run_tests.bat` | `scripts_install/run_tests.sh` |

---

## Problèmes fréquents (tous systèmes)

| Symptôme | Cause probable | Solution |
|---|---|---|
| Page carte affiche "Clé API Google Maps non configurée" | `GOOGLE_MAPS_API_KEY` vide dans `backend/.env` | Déjà pré-remplie dans cette livraison ; vérifiez qu'elle n'a pas été effacée |
| Paiement MTN MoMo échoue avec une erreur réseau | Le serveur qui héberge le backend ne peut pas joindre `sandbox.momodeveloper.mtn.com` en sortant | Vérifiez le pare-feu/proxy de votre hébergeur ou de votre réseau local ; testez avec `curl https://sandbox.momodeveloper.mtn.com` |
| Le frontend affiche une erreur de connexion à l'API | Le backend n'est pas démarré, ou `API_BASE_URL` incorrect dans `frontend/.env` | Démarrez le backend en premier |
