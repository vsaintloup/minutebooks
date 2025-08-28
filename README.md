# Détention en fidéicommis de livres de sociétés (LSAQ + LCSA) — Blueprint Django

Plateforme de **livres de société** numériques, bilingue (FR/EN), couvrant **LCSA (fédéral)** et **LSAQ (Québec)**. Ce dépôt fournit une base robuste (modèle de données, API, admin, i18n, stockage, déploiement) pour démarrer rapidement et évoluer vers la production.

> **Statut** : en construction (MVP). Code et schéma faits pour itérer vite, tout en gardant une trajectoire prod (S3, Postgres, Celery, permissions objet).

---

## Sommaire

* [Fonctionnalités clés](#fonctionnalités-clés)
* [Architecture & apps](#architecture--apps)
* [Stack & dépendances](#stack--dépendances)
* [Mise en route](#mise-en-route)

  * [Pré-requis](#pré-requis)
  * [Installation rapide (SQLite)](#installation-rapide-sqlite)
  * [PostgreSQL local (option)](#postgresql-local-option)
  * [Docker Compose (Postgres + Redis + MinIO)](#docker-compose-postgres--redis--minio)
  * [.env exemple](#env-exemple)
* [Commandes utiles](#commandes-utiles)
* [Modèle de données](#modèle-de-données)
* [API (aperçu)](#api-aperçu)
* [Internationalisation (FR/EN)](#internationalisation-fren)
* [Sécurité & conformité](#sécurité--conformité)
* [Déploiement](#déploiement)
* [Glossaire LSAQ/CBCA ↔ EN](#glossaire-lsaqcbca--en)
* [Feuille de route](#feuille-de-route)
* [Contribuer](#contribuer)
* [Licence](#licence)

---

## Fonctionnalités clés

* **Livre de société complet** : statuts, règlements, résolutions CA/actionnaires, registres (administrateurs/dirigeants, valeurs mobilières), documents divers.
* **Bilingue FR/EN** : interface et gabarits documentaires.
* **Multi-tenant** : organisations (cabinet) → sociétés clientes.
* **Documents** : upload, hash SHA‑256, catégories, export PDF/A (pipeline DOCX → PDF/A).
* **Registres valeurs mobilières** : classes d’actions, certificats, émissions/transferts/rachats, cap table calculée.
* **Tickets (portail client)** : demandes (rédaction, dépôts REQ/Corporations Canada, migration livre papier), pièces jointes.
* **Partage sécurisé** : liens lecture seule temporaires (data room) avec expiration.
* **Rappels** : échéances annuelles / événementielles (REQ, CC), Celery + Redis.
* **Audit** : historique & audit des modifications.

## Architecture & apps

```
minutebooks/
├─ minutebooks/          # settings, urls, asgi, wsgi
├─ accounts/             # User personnalisé
├─ orgs/                 # Organizations (cabinet) & memberships
├─ corps/                # Corporations (CBCA/QC), adresses, personnes/entités, dirigeants/administrateurs
├─ registers/            # Registres valeurs mobilières (classes, certificats, émissions/transferts/rachats)
├─ documents/            # Fichiers, catégories, hash, génération
├─ filings/              # Suivi dépôts (REQ/Corporations Canada), échéances
├─ tickets/              # Portail de demandes + pièces jointes
└─ billing/              # Abonnements (placeholder)
```

## Stack & dépendances

* **Django 5**, **Django REST Framework** (API), **django-allauth** (auth), **django-guardian** (permissions objet), **simple\_history**/**auditlog** (audit), **whitenoise** (static).
* **PostgreSQL** (prod) / **SQLite** (dev ultra‑rapide), **Redis** (Celery), **MinIO/S3** (stockage objet en prod), **boto3**, **django-storages**.
* Génération documentaire : **docxtpl**, **python-docx**, **pypdf2** (pipeline DOCX→PDF/A via LibreOffice en mode headless à brancher selon l’env).

## Mise en route

### Pré-requis

* Python 3.12+, `pip`, `virtualenv`
* (option) Docker Desktop/Engine pour `docker compose`

### Installation rapide (SQLite)

```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt  # ou voir Stack & dépendances

# Base SQLite + superuser
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# → http://127.0.0.1:8000/fr/admin (ou /en/admin)
```

### PostgreSQL local (option)

Créer l’utilisateur/BD puis configurer `.env` :

```env
DB_NAME=minutebooks
DB_USER=minutebooks
DB_PASSWORD=devpass
DB_HOST=127.0.0.1
DB_PORT=5432
```

Les settings lisent automatiquement `.env` (via `django-environ`).

### Docker Compose (Postgres + Redis + MinIO)

```bash
docker compose up -d db redis minio
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

> Console MinIO : [http://127.0.0.1:9001](http://127.0.0.1:9001) (user/pass par défaut cf. `.env`).

### .env exemple

Créez `.env` à la racine :

```env
# Django
SECRET_KEY=change-me-in-prod
DEBUG=True
ALLOWED_HOSTS=*

# DB (Postgres) – en dev vous pouvez garder SQLite
DB_NAME=minutebooks
DB_USER=minutebooks
DB_PASSWORD=devpass
DB_HOST=127.0.0.1
DB_PORT=5432

# S3 / MinIO (prod/dev optionnel)
USE_S3=False
AWS_STORAGE_BUCKET_NAME=minutebooks-dev
AWS_S3_REGION_NAME=ca-central-1

# Celery/Redis
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
```

## Commandes utiles

```bash
# Vérifier l’app
python manage.py check

# Migrations
python manage.py makemigrations [app]
python manage.py migrate [app] [target]     # --fake si table déjà présente en dev

# i18n
django-admin makemessages -l fr -l en
django-admin compilemessages

# Création d’un superuser
python manage.py createsuperuser
```

## Modèle de données

* **orgs** : `Organization`, `Membership` (rôles : OWNER, LAWYER, STAFF, CLIENT\_ADMIN, VIEWER)
* **corps** : `Corporation` (juridiction CBCA/QC, adresses de siège/dossiers), `Address`, `Party` (`Person`/`Entity`), `Director`, `Officer`
* **registers** : `ShareClass`, `ShareCertificate`, `ShareIssuance`, `ShareTransfer`, `ShareRedemption` (cap table via agrégations)
* **documents** : `Document` (catégories, `file`, `sha256`, auteur, langue)
* **filings** : `Filing` (types REQ/CC/ISC, statut, échéance)
* **tickets** : `Ticket` (+ `TicketAttachment`) — demandes client, statut, assignation

## API (aperçu)

* Auth par session/DRF token. Permissions objet via **django-guardian**.
* Endpoints typiques (selon configuration des `urls.py`) :

  * `/api/tickets/` : CRUD tickets (portail client)
  * `/api/corps/<id>/documents/` : documents d’une société
  * `/api/corps/<id>/cap-table/` : synthèse (si vue activée)

> Vérifiez `minutebooks/urls.py` et les `routers` DRF du projet pour l’exposition exacte.

## Internationalisation (FR/EN)

* `LANGUAGE_CODE = "fr"`, `LANGUAGES = [("fr"), ("en")]`, `LocaleMiddleware` activé.
* URLs i18n : `/fr/admin`, `/en/admin`.
* Templates et chaînes marquées `gettext` à compiler via `makemessages/compilemessages`.

## Sécurité & conformité

* **Prod** : `DEBUG=False`, `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` configurés, `SECRET_KEY` fort.
* Stockage **S3/MinIO** avec chiffrement côté serveur ; pistes d’audit (auditlog/simple\_history).
* Journal des accès aux partages (lecture seule) ; expiration des liens.

## Déploiement

* **Container** (OVHcloud/Render/Fly/Heroku‑like) :

  1. Image Python 3.12 + dépendances systèmes (LibreOffice si génération PDF/A).
  2. Variables d’env : DB Postgres managée, `USE_S3=True`, bucket S3 (ca‑central‑1), Redis managé.
  3. Collecte des fichiers statiques (Whitenoise ou S3), `migrate` au démarrage.
* **Static & Media** : statiques via Whitenoise (ou S3) ; **media** sur S3/MinIO.

## Glossaire LSAQ/CBCA ↔ EN

| FR (LSAQ/CBCA)             | EN (common law)    | Modèle                       |
| -------------------------- | ------------------ | ---------------------------- |
| Société par actions        | Corporation        | `corps.Corporation`          |
| Administrateur             | Director           | `corps.Director`             |
| Dirigeant                  | Officer            | `corps.Officer`              |
| Dénomination sociale       | Legal name         | `legal_name`                 |
| Nom d’emprunt              | Doing business as  | `doing_business_as`          |
| Siège / Siège statutaire   | Registered office  | `registered_office`          |
| Lieu des livres            | Records office     | `records_office`             |
| Catégorie/Classe d’actions | Share class        | `registers.ShareClass`       |
| Certificat d’actions       | Share certificate  | `registers.ShareCertificate` |
| Actionnaire (titulaire)    | Holder/Shareholder | `registers.*.holder`         |

## Feuille de route

* Cap table (vue + export), imports CSV pour migration.
* Génération de gabarits DOCX (résolutions annuelles, émissions, transferts, dividendes) FR/EN.
* Lien de partage lecture seule avec filigrane + log d’accès.
* Rappels (Celery beat) : REQ, CC, ISC/BUO.
* Intégration de signature (Notarius/DocuSign).

## Contribuer

* PRs bienvenues. Merci d’inclure **migrations** quand le schéma change.
* Respecter l’i18n (chaînes `gettext`) et la terminologie LSAQ/LCSA.

## Licence

Code sous **MIT** — voir `LICENSE`.
