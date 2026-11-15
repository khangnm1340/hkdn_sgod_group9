# OCR + Face Annotation Platform

A web-based, multi-user image annotation platform for creating and reviewing **OCR text regions** and **face bounding boxes**.

The project is being developed as a modular monolith: one React frontend, one Django REST Framework backend, one PostgreSQL database, and local filesystem storage for uploaded images and generated exports.

> **Project status:** Initial development / MVP. Features listed below describe the intended scope; they should not be considered implemented until their issues are completed and merged.

## Contents

- [Project goals](#project-goals)
- [MVP scope](#mvp-scope)
- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Repository structure](#repository-structure)
- [Requirements](#requirements)
- [Getting started](#getting-started)
  - [1. Clone the repository](#1-clone-the-repository)
  - [2. Configure environment variables](#2-configure-environment-variables)
  - [3. Start PostgreSQL](#3-start-postgresql)
  - [4. Set up the Django backend](#4-set-up-the-django-backend)
  - [5. Set up local file storage](#5-set-up-local-file-storage)
  - [6. Set up the React frontend](#6-set-up-the-react-frontend)
  - [7. Run the application](#7-run-the-application)
- [Common development commands](#common-development-commands)
- [Database and file storage](#database-and-file-storage)
- [API and annotation conventions](#api-and-annotation-conventions)
- [Testing and quality checks](#testing-and-quality-checks)
- [Contributing](#contributing)
- [AI-assisted development](#ai-assisted-development)
- [Version control: Git and Jujutsu](#version-control-git-and-jujutsu)
- [References](#references)

## Project goals

The platform provides a shared workspace where users can upload image datasets, annotate images, and review or export their work.

The main annotation types are:

- **OCR regions:** rectangular regions around text, with an editable Unicode transcription.
- **Face regions:** rectangular bounding boxes around faces, without a transcription field.

The first release focuses on reliable human annotation workflows. Automated OCR inference, face detection models, and other machine-learning features are not part of the initial MVP unless the project requirements are explicitly changed.

## MVP scope

### Planned features

- User registration/login and authenticated API access.
- Dataset creation and dataset membership management.
- Role-based permissions for dataset owners, annotators, and reviewers.
- Image upload and image metadata management.
- Browser-based annotation editor for OCR regions and face boxes.
- Create, retrieve, edit, and delete annotations.
- Basic annotation review (pending, approved, rejected), if retained in the agreed requirements.
- ZIP import with validation and a preview of errors before confirmation.
- Dataset export containing images and annotations.

### Not planned for the first MVP

- Automated OCR or face-detection inference.
- Video annotation.
- Polygon, brush, keypoint, or 3D annotation.
- Real-time collaborative editing of the same image.
- Cloud object storage integrations.
- Microservices, Kubernetes, or a distributed task queue.
- Multiple import/export formats beyond the format agreed in the specification.

Keep the first implementation small. Add infrastructure only when a demonstrated requirement justifies it.

## Technology stack

| Area | Technology | Responsibility |
|---|---|---|
| Frontend | React + TypeScript | Application UI and annotation editor |
| Frontend tooling | Vite | Development server and build tooling |
| Backend | Django 6.1 | Application framework and domain logic |
| API | Django REST Framework | REST endpoints, serializers, and permissions |
| Database | PostgreSQL 17 (development default) | Users, datasets, images' metadata, and annotations |
| Python dependencies | `uv` | Project dependencies, virtual environments, and lockfile |
| Image handling | Pillow | Reading image dimensions and validating image files |
| File storage | Local filesystem | Original images, staged imports, and exports |
| Container tooling | Docker Compose or Podman Compose | Reproducible local PostgreSQL service |
| Version control | Git-compatible remote; Git or Jujutsu locally | Collaboration and code review |

### Django version policy

This project targets the **Django 6.1 release series** (`Django>=6.1,<6.2`). The `uv.lock` file records the exact resolved patch versions used by the team. Update dependencies deliberately and run the backend test suite before committing a lockfile change.

Django 6.1's mainstream support is scheduled to end in **April 2027**; extended support is scheduled to end in **December 2027**. Django 6.1 supports Python 3.12–3.15 as of patch release 6.1.3. This project uses Python 3.14 by default; keep the `.python-version` file and `pyproject.toml` consistent across the team.

## Architecture

```text
Browser
  React + TypeScript
  ├── Authentication screens
  ├── Dataset management
  ├── Image viewer and annotation editor
  └── API client
          │ HTTP / JSON / multipart uploads
          ▼
Django + Django REST Framework
  ├── accounts       users and authentication
  ├── datasets       datasets, memberships, and images
  ├── annotations    OCR regions and face boxes
  └── imports        import validation and export serialization
          │                         │
          ▼                         ▼
PostgreSQL                    Local filesystem
  users                       uploaded images
  datasets                    staged import files
  memberships                 generated exports
  image metadata
  annotations
```

The database stores metadata and file paths, not image bytes. Uploaded files live under the backend's media directory. The backend is authoritative for authentication, permissions, geometry validation, import validation, and persistence; frontend validation is only for immediate user feedback.

## Repository structure

The intended structure as the project grows:

```text
annotation-platform/
├── backend/
│   ├── config/                 # Django project settings and URL configuration
│   ├── accounts/               # Custom user model and authentication
│   ├── datasets/               # Datasets, memberships, and images
│   ├── annotations/            # OCR and face annotations
│   ├── imports/                # ZIP validation, import, and export
│   ├── media/                  # Local uploaded files (not committed)
│   ├── pyproject.toml          # Python dependencies managed by uv
│   ├── uv.lock                 # Exact resolved Python dependencies
│   └── manage.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── package-lock.json
├── docs/
│   ├── architecture.md
│   ├── database-and-api-spec.md
│   └── annotation-guidelines.md
├── tests/
│   └── fixtures/               # Small synthetic test datasets only
├── .agents/                    # Optional project-specific agent skills
├── .github/workflows/           # CI workflows
├── AGENTS.md                   # Shared instructions for coding agents
├── .env.example
├── .gitignore
├── compose.yaml                # Local PostgreSQL service
└── README.md
```

The exact structure may evolve, but changes to the architecture or API contract must be reflected in `docs/`.

## Requirements

Install the following tools before setting up the project:

- [Python 3.14](https://www.python.org/) (or let `uv` install a compatible interpreter).
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python dependency management.
- [Node.js](https://nodejs.org/) and npm for the frontend. Use a Node.js version supported by the installed Vite release.
- [Docker Engine + Docker Compose](https://docs.docker.com/compose/) **or** [Podman + Podman Compose](https://podman.io/).
- Git or [Jujutsu](https://jj-vcs.github.io/jj/) for version control.

Check the installed tools:

```bash
python --version
uv --version
node --version
npm --version
podman --version  # or: docker --version
```

## Getting started

The commands below assume the repository has already been scaffolded and contains the files shown above. If you are the person creating the initial scaffold, use the commands in [Initial scaffolding](#initial-scaffolding) first.

### 1. Clone the repository

Using Git:

```bash
git clone <repository-url>
cd annotation-platform
```

If you use Jujutsu locally, you can work with the repository through its Git-compatible integration. See [Version control: Git and Jujutsu](#version-control-git-and-jujutsu).

### 2. Configure environment variables

Copy the example environment file and update the local development values:

```bash
cp .env.example .env
```

Example `.env.example`:

```dotenv
# PostgreSQL container
POSTGRES_DB=annotation_platform
POSTGRES_USER=annotation_app
POSTGRES_PASSWORD=change-this-local-password

# Django connection to PostgreSQL on the host
DATABASE_URL=postgresql://annotation_app:change-this-local-password@127.0.0.1:5432/annotation_platform

# Django development settings
DJANGO_SECRET_KEY=replace-this-with-a-local-development-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

Use the same database name, username, and password in `POSTGRES_*` and `DATABASE_URL`. The `.env` file is for local development only and must never be committed. Do not reuse the example secret or password in a deployed environment.

### 3. Start PostgreSQL

The root `compose.yaml` should define a PostgreSQL service with a persistent named volume. Start it with Podman:

```bash
podman compose up -d db
podman compose ps
podman compose logs -f db
```

Or use Docker Compose:

```bash
docker compose up -d db
docker compose ps
docker compose logs -f db
```

Wait until the database health check reports healthy before starting Django migrations. PostgreSQL data is persisted in a named volume; stopping or recreating the container should not delete that volume. **Do not use `down -v` unless you intentionally want to delete the local database.**

### 4. Set up the Django backend

From the repository root:

```bash
cd backend
uv sync
```

`uv sync` creates or updates the project's virtual environment from `pyproject.toml` and `uv.lock`. The lockfile should be committed so all contributors resolve the same dependency versions.

Run Django checks:

```bash
uv run python manage.py check
```

**Important:** Before the first `migrate`, implement the custom user model in `accounts` and configure:

```python
AUTH_USER_MODEL = "accounts.User"
```

Changing Django's user model after the initial migrations is difficult. Confirm the custom user model and database settings before creating the first migration.

After the initial models and settings are ready:

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

Start the backend development server:

```bash
uv run python manage.py runserver
```

The API is expected to be available at `http://127.0.0.1:8000/` during local development.

### 5. Set up local file storage

Create local media directories if they do not exist:

```bash
mkdir -p backend/media/uploads
mkdir -p backend/media/staging
mkdir -p backend/media/exports
```

Configure Django's filesystem storage in its settings:

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

- `uploads/` stores original uploaded images.
- `staging/` stores temporary import archives while they are validated.
- `exports/` stores generated export files when needed.

The database stores the relative file name/path and image metadata. It does not store the actual image bytes. The `backend/media/` directory must be ignored by Git and backed up separately from PostgreSQL.

Uploaded datasets are private application data. Do not expose the media directory as unrestricted public static files. Image download endpoints must check that the requesting user has permission to access the image's dataset.

### 6. Set up the React frontend

In a separate terminal:

```bash
cd frontend
npm ci
```

If `package-lock.json` has not been created yet, run `npm install` once and commit the generated lockfile. For normal contributor setup, prefer `npm ci` so the exact dependency tree in the lockfile is installed.

Start the Vite development server:

```bash
npm run dev
```

The frontend is expected to be available at `http://localhost:5173/` during local development.

### 7. Run the application

You will normally use three terminals:

**Terminal 1 — PostgreSQL** (from the repository root):

```bash
podman compose up -d db
```

**Terminal 2 — Django** (from `backend/`):

```bash
uv run python manage.py runserver
```

**Terminal 3 — React** (from `frontend/`):

```bash
npm run dev
```

The React development origin must be included in Django's CORS allowlist (for example, `http://localhost:5173`). Keep CORS restricted to known frontend origins; do not use a wildcard as a shortcut for credentialed requests.

## Initial scaffolding

These commands are for the initial repository setup, not something every contributor needs to repeat.

### Create the repository skeleton

```bash
mkdir annotation-platform
cd annotation-platform

mkdir -p backend frontend docs tests/fixtures .github/workflows .agents/skills
touch README.md .gitignore AGENTS.md .env.example
```

### Bootstrap Django with uv

```bash
cd backend

# Create a minimal uv-managed Python project.
uv init --bare --python 3.14
uv python pin 3.14

# Runtime dependencies.
uv add "Django>=6.1,<6.2" djangorestframework "psycopg[binary]" Pillow django-environ django-cors-headers drf-spectacular

# Development and test dependencies.
uv add --dev pytest pytest-django pytest-cov ruff

# Generate the Django project and domain apps.
uv run django-admin startproject config .
uv run python manage.py startapp accounts
uv run python manage.py startapp datasets
uv run python manage.py startapp annotations
uv run python manage.py startapp imports
```

The version range keeps the project on the Django 6.1 series; `uv.lock` records the exact resolved versions. Do not create initial migrations until the custom User model is configured.

The API contract currently describes JWT authentication. Choose and integration-test the JWT package against the selected Django/DRF versions before relying on it; add it with `uv add <package>` once that compatibility check is part of the backend setup.

### Bootstrap React with Vite

From the repository root:

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

Commit `package-lock.json` so teammates can use `npm ci`.

### Add frontend packages when needed

Install additional packages when implementing their corresponding feature, not all at once:

```bash
cd frontend

# Client-side routing and API data fetching.
npm install react-router-dom @tanstack/react-query

# Canvas-based annotation editor.
npm install konva react-konva
```

## Common development commands

Run these from the relevant project directory.

### Backend (`backend/`)

```bash
uv sync                                  # Sync dependencies from uv.lock
uv add <package>                         # Add a runtime dependency
uv add --dev <package>                  # Add a development dependency
uv remove <package>                      # Remove a dependency
uv lock                                  # Resolve/update the lockfile
uv run python manage.py check            # Check Django configuration
uv run python manage.py makemigrations   # Create migration files
uv run python manage.py migrate          # Apply migrations
uv run python manage.py test             # Run Django tests
uv run pytest                            # Run pytest suite, if configured
uv run ruff check .                      # Lint Python code
uv run ruff format .                     # Format Python code
```

### Frontend (`frontend/`)

```bash
npm install                              # Install/update dependencies
npm ci                                   # Clean install from package-lock.json
npm run dev                              # Start development server
npm run lint                             # Run ESLint (if configured by the Vite template)
npm run build                            # Build production assets
npm run preview                          # Preview production build
```

## Database and file storage

- PostgreSQL is the source of truth for application records.
- Image binaries, staged import archives, and generated exports live in local filesystem storage during development.
- The application stores paths/keys and metadata in PostgreSQL, not the binary image content.
- Do not commit database volumes, uploaded images, export archives, `.env` files, or secrets.
- Back up PostgreSQL and the media directory together; they represent different parts of the application's data.
- For a deployment with multiple backend instances, local storage must be replaced by shared storage or a shared persistent volume. Local storage is the development/MVP choice, not a claim that arbitrary local disks can be shared between servers.

## API and annotation conventions

The detailed database schema and endpoint definitions belong in `docs/database-and-api-spec.md`. Keep that document as the canonical contract for frontend/backend integration.

Key conventions:

1. API routes are versioned under `/api/v1/`.
2. IDs are UUIDs and timestamps use ISO-8601.
3. OCR annotations contain a transcription; face annotations do not.
4. Bounding boxes use original-image pixel coordinates, with `(x1, y1)` as the top-left and `(x2, y2)` as the bottom-right.
5. Coordinates must satisfy `0 <= x1 < x2 <= image.width` and `0 <= y1 < y2 <= image.height`.
6. The backend validates permissions, geometry, file content, and imported data. Frontend validation is not a security boundary.
7. Annotation updates use a version number to detect stale edits instead of silently overwriting another user's work.
8. Import must validate an archive before creating dataset records. Failed imports must not leave a partial dataset.
9. Import/export uses the documented, versioned interchange format. Do not silently change its shape; update the API/schema documentation and tests when it changes.

## Testing and quality checks

Tests should protect annotation data from corruption and accidental overwrites.

At minimum, cover:

- custom user creation and authentication;
- dataset membership and role permissions;
- valid/invalid image uploads;
- OCR and face annotation creation and validation;
- bounding-box boundaries and image-coordinate conversions;
- stale annotation versions and conflict responses;
- ZIP path traversal, invalid archives, duplicate names, missing image references, and invalid coordinates;
- import/export round trips using small synthetic fixtures;
- frontend drawing, saving, reloading, and editing of annotations.

Use synthetic test images and archives. Do not commit private, real, or sensitive face images to the repository.

## Contributing

1. Read the relevant requirements and the API/schema contract before changing code.
2. Work on one small issue or vertical slice at a time.
3. Keep changes focused; avoid unrelated refactoring in feature branches.
4. Add or update tests with the implementation.
5. Update documentation when the schema, API, or user-visible workflow changes.
6. Open a pull request for review and explain what changed, how it was tested, and any remaining limitations.
7. Do not merge code that has not been reviewed or does not pass the required checks.

Suggested branch/commit areas include `accounts`, `datasets`, `annotations`, `imports`, `frontend`, `tests`, and `docs`.

## AI-assisted development

AI coding tools may be used to implement issues, but generated code is not automatically correct or accepted.

- Read `AGENTS.md` and the relevant skill in `.agents/skills/` before starting a task.
- Give the agent a narrow task with acceptance criteria and relevant API/schema references.
- Ask for tests and a summary of the files changed.
- Review the diff and run the tests locally before opening a pull request.
- Do not let an agent change the database schema or API contract without updating the corresponding documentation and migrations.
- A team member remains responsible for understanding, testing, and maintaining every merged change.

## Version control: Git and Jujutsu

The repository uses a Git-compatible remote for collaboration. Contributors may use Git or Jujutsu (`jj`) locally; using Jujutsu is optional and does not change the application architecture.

- Follow the team's agreed branch/bookmark and pull-request workflow.
- Push work to the shared Git-compatible remote so teammates can review it.
- Do not commit local tool state, virtual environments, build output, or uploaded data.
- If using Jujutsu, coordinate the remote bookmark/branch workflow with the team before pushing shared work.

## References

- [Django 6.1 documentation](https://docs.djangoproject.com/en/6.1/)
- [Django supported versions and support schedule](https://www.djangoproject.com/download/)
- [Django REST Framework documentation](https://www.django-rest-framework.org/)
- [uv documentation](https://docs.astral.sh/uv/)
- [Vite documentation](https://vite.dev/guide/)
- [PostgreSQL documentation](https://www.postgresql.org/docs/)
- [Jujutsu documentation](https://jj-vcs.github.io/jj/)
