# Gestion de Cimetière GI2 2026 — v2

Application web professionnelle de gestion numérique pour le **Cimetière
Municipal de Vindoulou** (Pointe-Noire, République du Congo).

Réécriture complète de la version précédente (Supabase/React) vers un stack
maîtrisé de bout en bout :

> 🚀 **Installation rapide** : voir [`INSTRUCTIONS.md`](./INSTRUCTIONS.md) —
> un script (`scripts_install/setup.sh`) automatise tout l'essentiel.
>
> 🔑 **Identifiants pré-configurés** : `backend/.env` contient déjà votre
> clé Google Maps et vos identifiants MTN MoMo sandbox. Il ne vous reste
> qu'à renseigner `DB_NAME`/`DB_USER`/`DB_PASSWORD` avec votre PostgreSQL.
> ⚠️ Ce fichier contient des secrets réels : ne le committez jamais dans un
> dépôt Git public, et régénérez ces clés avant un déploiement en
> production professionnelle.

- **Backend** : Django 5.2 LTS + Django Ninja 1.6 (API REST) + PostgreSQL
- **Frontend** : Flet 0.85.3 (Python, mode web) + `flet-web` + `flet-webview`
- **Paiements** : enregistrement manuel + intégration MTN Mobile Money (Collections API)
- **Carte** : Google Maps JavaScript API (marqueurs par statut, filtres, contour du site)
- **Authentification** : JWT (access + refresh), rôles admin / gestionnaire / agent
- **Documents** : reçus de paiement et exports en PDF (ReportLab)
- **Audit** : journal complet des actions (création/modification/suppression/connexion)

---

## 1. Structure du projet

```
cimetiere_gi2/
├── backend/          # API Django + Django Ninja
│   ├── apps/
│   │   ├── accounts/       # Utilisateurs, JWT, rôles
│   │   ├── cemetery/       # Sections, Blocs, Caveaux, Défunts, carte
│   │   ├── reservations/   # Réservations de caveaux
│   │   ├── concessions/    # Concessions funéraires (10/30 ans, perpétuelle)
│   │   ├── exhumations/    # Suivi des exhumations
│   │   ├── payments/       # Paiements manuels + MTN MoMo + reçus PDF
│   │   ├── notifications/  # Notifications internes
│   │   ├── audit/          # Journal d'audit
│   │   └── core/           # Utilitaires partagés (permissions, pagination...)
│   ├── config/             # Settings, urls, wsgi/asgi
│   ├── scripts/
│   │   └── regression_test.py   # Suite de tests end-to-end de l'API
│   ├── api.py               # Point d'entrée Django Ninja (agrège tous les routeurs)
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/          # Application Flet (mode web)
    ├── app/
    │   ├── components/     # Thème, layout, tableaux, dialogues réutilisables
    │   ├── pages/           # Une page par écran (Login, Dashboard, Sections...)
    │   ├── services/        # Client API + services par domaine métier
    │   └── state/            # Contexte de session (par connexion, voir §5)
    ├── scripts/
    │   └── test_pages.py     # Harnais de test de construction des pages
    ├── main.py
    ├── requirements.txt
    └── .env.example
```

---

## 2. Installation — Backend

> 💻 **Sous Windows ?** Les commandes ci-dessous sont pour macOS/Linux. Utilisez
> plutôt `scripts_install\setup.bat` — voir [`INSTRUCTIONS.md`](./INSTRUCTIONS.md#windows)
> pour la marche à suivre complète et les équivalents Windows de chaque commande.

### 2.1. Prérequis
- Python 3.11+
- PostgreSQL 14+

### 2.2. Base de données PostgreSQL

```sql
CREATE DATABASE cimetiere_gi2;
CREATE USER cimetiere_user WITH PASSWORD 'un_mot_de_passe_fort';
GRANT ALL PRIVILEGES ON DATABASE cimetiere_gi2 TO cimetiere_user;
```

### 2.3. Installation Python

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Éditez `.env` et renseignez au minimum :
- `DJANGO_SECRET_KEY` et `JWT_SECRET_KEY` (chaînes aléatoires longues et uniques)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `CORS_ALLOWED_ORIGINS` (URL du frontend, ex: `http://localhost:8550`)

### 2.4. Migrations et premier compte admin

```bash
python manage.py migrate
python manage.py bootstrap_admin --email admin@cimetiere.cg --password VotreMotDePasseFort123 --full-name "Nom Complet"
```

### 2.5. Lancer le serveur (développement)

```bash
python manage.py runserver 0.0.0.0:8000
```

L'API est alors disponible sur `http://localhost:8000/api`.

### 2.6. Lancer le serveur (production)

```bash
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

Placez un reverse proxy (nginx/Caddy) devant Gunicorn avec HTTPS obligatoire
(les jetons JWT et les callbacks MTN MoMo ne doivent jamais transiter en HTTP
non chiffré en production).

---

## 3. Configuration MTN Mobile Money

1. Créez un compte sur https://momodeveloper.mtn.com et souscrivez au produit
   **Collections**.
2. Récupérez votre `Ocp-Apim-Subscription-Key` (clé d'abonnement sandbox ou
   production).
3. Générez un `API User` + `API Key` (voir la documentation MTN — un script
   d'aide peut être ajouté dans `scripts/` si besoin).
4. Renseignez dans `.env` :
   ```
   MOMO_SUBSCRIPTION_KEY=...
   MOMO_API_USER=...
   MOMO_API_KEY=...
   MOMO_BASE_URL=https://sandbox.momodeveloper.mtn.com   # ou l'URL de production
   MOMO_TARGET_ENVIRONMENT=sandbox                          # ou "mtncongo" en prod
   MOMO_CALLBACK_HOST=https://votre-domaine-public.com       # requis pour les callbacks
   ```

Tant que ces variables ne sont pas renseignées, les tentatives de paiement
MoMo échouent proprement avec un message explicite (aucun crash).

**Important — accès réseau sortant** : le serveur backend doit pouvoir
joindre `sandbox.momodeveloper.mtn.com` (puis le domaine de production MTN
le moment venu) en HTTPS sortant. Si votre hébergeur restreint les accès
sortants (pare-feu, proxy d'entreprise, certains PaaS), autorisez ce domaine
explicitement — sinon les paiements échoueront avec une erreur réseau claire
plutôt qu'un plantage.

---

## 4. Configuration Google Maps (carte interactive)

1. Créez une clé sur https://console.cloud.google.com/google/maps-apis
2. Activez l'API **Maps JavaScript API**.
3. Restreignez la clé par référent HTTP (domaine de votre backend) en production.
4. Renseignez dans `.env` du backend :
   ```
   GOOGLE_MAPS_API_KEY=votre_cle
   ```

Les coordonnées du site (centre + points de repère) sont déjà configurées
dans `settings.py` avec les valeurs exactes du Cimetière Municipal de
Vindoulou. Sans clé configurée, la page carte affiche un message d'instruction
clair au lieu d'une erreur.

**Note de conception** : la carte est une page HTML servie par le backend
Django (`/cimetiere/carte-embed/`) et affichée dans le frontend Flet via le
contrôle `WebView` (paquet `flet-webview`). Ce découpage a été choisi car
Flet ne fournit pas de contrôle cartographique natif ; la carte reste ainsi
consultable même hors de l'app Flet, en accédant directement à cette URL.

---

## 5. Installation — Frontend (Flet)

> 💻 **Sous Windows ?** Voir [`INSTRUCTIONS.md`](./INSTRUCTIONS.md#windows) pour
> les commandes équivalentes (`scripts_install\setup.bat`).

```bash
cd frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Éditez `.env` :
```
API_BASE_URL=http://localhost:8000/api
FLET_PORT=8550
```

Lancement :
```bash
python main.py
```

L'application est accessible sur `http://localhost:8550`.

### 5.1. Point d'architecture important — isolation multi-utilisateurs

Flet en mode web gère plusieurs connexions simultanées dans le même
processus serveur. **Aucune variable globale ne stocke de jeton ou d'état
utilisateur** : chaque connexion crée sa propre instance de
`SessionContext` (voir `app/state/session_context.py`), garantissant qu'un
utilisateur ne peut jamais voir les données ou le jeton JWT d'un autre. La
session survit toutefois à un rafraîchissement de page grâce au refresh
token stocké dans `client_storage` (côté navigateur, propre à chaque onglet).

---

## 6. Déploiement en production (aperçu)

| Composant | Recommandation |
|---|---|
| Backend | Gunicorn/Uvicorn derrière nginx, HTTPS obligatoire |
| Base de données | PostgreSQL managé (sauvegardes automatiques) |
| Frontend | `flet build web` pour générer des fichiers statiques déployables sur n'importe quel serveur web, **ou** garder `main.py` derrière un process manager (systemd/supervisor) |
| Variables sensibles | Jamais commitées ; utiliser les secrets du fournisseur d'hébergement |
| CORS | Restreindre `CORS_ALLOWED_ORIGINS` au domaine réel du frontend |
| MTN MoMo | Basculer `MOMO_BASE_URL` et `MOMO_TARGET_ENVIRONMENT` vers la production une fois validé en sandbox |

---

## 7. Tests

### Backend (régression API complète — 53 scénarios)
```bash
cd backend
# Nécessite un serveur de développement lancé sur le port utilisé par le script
python scripts/regression_test.py
```

### Frontend (construction de toutes les pages contre l'API réelle)
```bash
cd frontend
python scripts/test_pages.py
```

---

## 8. Comptes et rôles

| Rôle | Permissions |
|---|---|
| **agent** | Lecture/écriture sur sections, blocs, caveaux, défunts, réservations, exhumations. Pas d'accès aux paiements/concessions/utilisateurs/audit. |
| **gestionnaire** | Tout ce que fait l'agent + validation des réservations, gestion des concessions et des paiements. |
| **admin** | Accès total, y compris suppression, gestion des utilisateurs et journal d'audit. |

La recherche publique de défunts (`/recherche`) ne nécessite aucune
authentification.

---

## 9. Robustesse des saisies numériques

**Bug corrigé** : saisir un montant ou une superficie avec un espace comme
séparateur de milliers (ex: `3 800`) faisait planter l'application avec une
`ValueError` non gérée (`float("3 800")` échoue en Python). Tous les champs
numériques (superficie, montants, latitude, longitude) passent maintenant
par un parseur commun (`app/utils.py::parse_float`) qui :

- tolère l'espace normal et l'espace insécable comme séparateur de milliers
  (`3 800`, `3 800`) ;
- tolère la virgule décimale française (`3800,50`) ;
- refuse proprement (message clair, formulaire reste ouvert) toute saisie
  réellement invalide, plutôt que de faire planter l'application ;
- valide des bornes optionnelles (ex: latitude entre -90 et 90).

**Filet de sécurité supplémentaire** : `form_dialog` et `confirm_dialog`
capturent désormais toute exception imprévue dans la logique de sauvegarde
ou de confirmation — même un bug non anticipé affiche un message d'erreur
au lieu de laisser l'interface silencieusement figée. La trace complète
reste journalisée en console pour le diagnostic.

Un test de non-régression dédié (`scripts/test_pages.py` ->
`run_input_robustness_tests`) reproduit exactement le cas signalé (`3 800`
dans le champ Superficie d'une section) pour éviter toute réapparition du
bug.

---

## 10. Correctif critique — API de dialogue Flet 0.85.3 + refonte responsive

**Bug racine identifié et corrigé** : Flet 0.85.3 a remplacé l'ancienne API
`page.dialog = mon_dialogue; mon_dialogue.open = True; page.update()` par
`page.show_dialog(mon_dialogue)`. L'ancien pattern ne lève aucune erreur (il
crée juste un attribut fantôme ignoré par le moteur de rendu) — ce qui
expliquait que les boutons "Nouvelle section", "Nouveau bloc", "Nouveau
caveau", "MTN MoMo", etc. ne faisaient visuellement rien, sans aucune erreur
ni côté frontend ni côté backend. Tous les dialogues (formulaires,
confirmations, notifications) ont été corrigés pour utiliser l'API moderne,
et pour fermer explicitement leur propre instance de dialogue (plutôt que de
compter sur "le dernier dialogue ouvert", ambigu dès qu'une notification
apparaît juste avant la fermeture d'un formulaire).

**Refonte responsive complète** :
- Barre latérale permanente uniquement à partir de 768px de largeur.
- En dessous de 768px : tiroir de navigation natif Flet (`NavigationDrawer`),
  ouvert via une icône ☰ dans la barre supérieure, avec recouvrement
  (scrim) et fermeture automatique après navigation — géré nativement par
  Flet, pas de réimplémentation manuelle du menu burger.
- Bascule en direct entre les deux modes lors du redimensionnement de la
  fenêtre (`page.on_resize`), sans recharger la page.
- En-têtes de page (`page_header`) qui passent en colonne (titre au-dessus
  du bouton) plutôt que de se chevaucher sur petit écran.
- Largeur des formulaires/dialogues adaptative (`responsive_width`),
  corrigée pour lire la vraie propriété `page.width` (l'ancienne
  implémentation lisait `page.window_width`, qui n'existe pas en 0.85.3 et
  rendait la fonction inopérante).

**Icône** : le sapin (`PARK_OUTLINED`) a été remplacé par une icône d'église
(`CHURCH_OUTLINED`) sur la page de connexion, la recherche publique et la
barre latérale — Material Icons ne propose pas de pierre tombale, l'église
est le symbole le plus proche disponible pour un lieu de mémoire.

**Filtre ajouté** : la page Utilisateurs dispose maintenant d'un filtre par
rôle, cohérent avec les autres pages de liste (Caveaux, Journal d'audit).

---

## 11. Nouveautés de l'itération précédente

- **Export CSV** : en plus du PDF, les paiements (`Paiements` → bouton
  "CSV") et le journal d'audit (`Journal d'audit` → bouton "Exporter en
  CSV") peuvent être exportés en CSV (encodage UTF-8 avec BOM, compatible
  Excel).
- **Notifications** : une cloche dans la barre supérieure affiche le nombre
  de notifications non lues et permet de les consulter/marquer comme lues.
  Des notifications sont créées automatiquement lors de :
  - une nouvelle réservation en attente (→ gestionnaires/admin)
  - la validation ou le refus d'une réservation (→ son créateur)
  - un nouveau paiement enregistré, manuel ou MTN MoMo (→ gestionnaires/admin)
  - la confirmation d'un paiement MTN MoMo (→ l'agent qui l'a initié)
  - la fin d'une exhumation (→ son créateur)
- **Réinitialisation de mot de passe par un admin** : dans `Utilisateurs`,
  une icône clé permet à un administrateur de définir un nouveau mot de
  passe pour n'importe quel compte (utile en cas d'oubli), sans connaître
  l'ancien.
- **Camembert réel dans Analytique** : Flet 0.85.3 ne fournissant pas de
  contrôle `PieChart` natif, un camembert est dessiné directement avec
  `flet.canvas` (répartition des caveaux par statut, répartition des
  réservations par statut).
