# OCR labeling MVP: architecture and repository bootstrap

## Should you copy CVAT's architecture?

Use CVAT as a **reference**, but do not reproduce its full architecture for this MVP. CVAT supports many modalities, large deployments, integrations, workers, and operational requirements. An image-only OCR college project does not need most of that complexity. Copy the useful boundaries and concepts: keep import logic separate from annotation logic, keep the browser UI separate from data validation and persistence, define one canonical annotation format, and test import/export behavior. Implement those ideas in a small application that your group can run and explain.

Recommended first version:

- one Git repository;
- one web application, with backend and frontend modules in the same repository;
- one relational database (SQLite for local development; PostgreSQL if you deploy for multiple users);
- local media storage for development;
- no microservices, Kubernetes, model server, or queue at the start;
- synchronous import for small packages, with clear size limits. Add a background worker only if real imports take too long.

Pick a stack your group or course can support. One reasonable default is **Django + Django REST Framework + PostgreSQL + React/TypeScript**. Django gives you authentication, database migrations, admin tooling, and a clear backend structure. If the group already knows another stack, familiarity is more valuable than this particular choice. Avoid splitting into multiple repositories or services until there is a demonstrated reason.

## MVP scope

The MVP should support:

1. Uploading a ZIP of images, with optional ICDAR-style text-region annotations.
2. Validating the archive and previewing import errors before creating the dataset.
3. Displaying an image and its existing OCR regions.
4. Drawing and editing rectangular or polygon text regions (choose one shape first; rectangles are simpler).
5. Entering and editing the transcription for each region.
6. Saving, reopening, and deleting annotations.
7. Exporting images and annotations in one documented format, preferably matching the first import format.
8. A minimal multi-user workflow: sign in, see assigned datasets, and avoid silently overwriting another person's edits.

Leave OCR model inference, video, face/person/vehicle labels, complex review analytics, cloud storage integrations, and multi-format support outside the first milestone.

## Architecture

```text
Annotator's browser
  ├─ Dataset list and import form
  ├─ OCR image editor (canvas + transcription fields)
  └─ API client
           |
           v
Web backend (single application)
  ├─ Authentication and dataset/task endpoints
  ├─ Import validator and format adapter
  ├─ Annotation validation and persistence
  └─ Export format adapter
      |                    |
      v                    v
Relational database     Image/file storage
users, datasets,        original uploads, extracted images,
items, regions,         generated exports
transcriptions
```

The backend is the authority for validation and saving. The frontend can give immediate feedback, but must not be the only place that checks geometry, permissions, or import correctness. The source image files live in file/object storage; the database stores their metadata and paths/keys, not the image bytes themselves.

### Backend modules

- **Accounts:** users and basic roles. For a course prototype, account creation can be limited to the team.
- **Datasets and images:** dataset metadata, source image records, checksums, dimensions, and storage keys.
- **OCR annotations:** geometry, transcription, optional language, and timestamps/author. Use an explicit schema rather than a generic shape with arbitrary fields.
- **Import:** archive inspection, format parsing, validation report, and dataset creation.
- **Export:** serialize canonical records to the selected output format.

These are modules in one backend, not separate network services.

### Minimal data model

One possible starting schema:

```text
Dataset(id, name, created_by, created_at)
Image(id, dataset_id, filename, storage_key, width, height, checksum)
OCRRegion(id, image_id, geometry, transcription, created_by, updated_at, version)
```

Keep coordinates in original-image pixel units and document the geometry convention. For a rectangle, store `x1, y1, x2, y2`; require `0 <= x1 < x2 <= width` and `0 <= y1 < y2 <= height`. If using polygons, require at least three valid points and check that points lie within image bounds. Store transcription as Unicode text. Decide whether an empty transcription is allowed and test that choice.

Add dataset assignment/review tables only when the MVP workflow needs them. If multiple annotators may edit one image, use a version number (optimistic concurrency): a save based on an old version should return a conflict and ask the user to reload/resolve it instead of erasing newer work.

### Import contract

Write down exactly what the first import accepts. For example: a ZIP containing supported image files and, optionally, an ICDAR localization annotation file. Specify filename matching, character encoding, coordinate order, supported geometry, and what happens to unknown fields.

Import flow:

1. Upload to a temporary/staging location.
2. Enforce upload size, file-count, and image-type limits; inspect actual file content rather than trusting extensions alone.
3. Safely inspect ZIP entries and reject path traversal, nested archives, and suspicious expansion sizes.
4. Parse images and optional annotations; report missing images, duplicate names, malformed rows, invalid coordinates, and unsupported records.
5. Show a preview/validation summary. Do not partially create a dataset on a failed import.
6. On confirmation, save dataset metadata and extracted images, then create normalized OCR regions.

For the first MVP, a clear validation report matters more than supporting many variants. Do not silently drop records.

### Annotation save flow

```text
User draws/edits region and enters transcription
  → frontend validates obvious mistakes for quick feedback
  → API checks authentication, permissions, geometry and version
  → database saves region and increments its version
  → API returns canonical saved record
  → frontend shows saved state
```

Auto-save can be added, but make pending/saved/error states visible. A Save button is acceptable for the first version if it prevents navigation from discarding edits.

## Testing plan

Start tests with the behaviors that can lose or corrupt student annotation data:

- **Unit tests:** import parser, filename matching, geometry bounds, Unicode transcription handling, and export serialization.
- **Fixture tests:** a tiny known ZIP imports into exact expected images/regions and exports to expected files. Include malformed rows, duplicate files, missing images, and invalid coordinates.
- **API tests:** upload/validate/confirm, create/update/delete a region, permission checks, stale-version conflict, and export download.
- **UI tests:** import a sample dataset, open an image, draw a region, enter text, save, navigate away and back, and verify it persists.
- **One end-to-end smoke test:** run the application in its normal local deployment and complete one import-label-export round trip.

Use synthetic fixtures only; do not commit private or real face data. Each feature should include acceptance criteria and tests. Configure GitHub Actions (or your Git host's CI) to run formatting/lint, type checks where applicable, and tests on every pull request. Protect the main branch so changes are reviewed and checks pass before merging.

Do not ask AI to “make the app” in one prompt. Give it small tasks: one importer behavior, one API endpoint, one UI flow. Supply acceptance criteria, ask for tests, inspect the diff, and run the documented checks. Keep a human responsible for deciding whether behavior matches the labeling rules.

## Initial repository setup

The commands below assume the project will use GitHub and Django + React. Run them in a new project directory, **not inside the CVAT checkout**. Replace `YOUR-ORG/YOUR-REPO` and `your-github-username` with your own values. These are a starting skeleton; do not generate a full application scaffold before the group agrees on its scope and stack.

### 1. Create and initialize the project directory

```bash
mkdir ocr-labeling-mvp
cd ocr-labeling-mvp
git init -b main
```

Create the initial structure:

```bash
mkdir -p backend frontend docs tests/fixtures
touch README.md .gitignore
```

Suggested structure as the project grows:

```text
ocr-labeling-mvp/
├── backend/              # Django project and domain apps
├── frontend/             # React/TypeScript application
├── docs/                 # requirements, label guide, decisions
├── tests/fixtures/       # tiny synthetic import/export examples
├── .github/workflows/    # automated checks
├── .gitignore
└── README.md
```

### 2. Write the README before implementation

The first README should state:

- what problem the MVP solves and who uses it;
- the exact first-release features and explicit out-of-scope items;
- the chosen stack and supported import/export format;
- prerequisites and copy-paste local setup/run/test commands (fill these in as the app is scaffolded);
- where sample data lives and confirmation that fixtures are synthetic;
- how to propose work, review changes, and report bugs.

Do not leave setup commands as guesses. Verify each command on a clean checkout before calling the README complete.

### 3. Add team and project rules

Create a GitHub repository, initially private if the project contains any non-public sample data. Add collaborators with their own accounts rather than sharing credentials. Turn on pull requests, require at least one teammate review, and require CI checks before merging once CI exists. Keep all test/sample data synthetic and never commit secrets or `.env` files.

Use a simple contribution process:

```text
Issue with expected behavior and acceptance examples
  → small feature branch
  → implementation plus tests
  → pull request and human review
  → passing automated checks
  → merge to main
```

Create a `.gitignore` appropriate for Python, Node, editors, local databases, uploaded data, build output, and secrets. Review it before the first commit so datasets and credentials do not enter Git history.

### 4. Connect the GitHub remote

Create an empty repository on GitHub (do not have GitHub pre-create a README if you already made one locally), then run:

```bash
git add README.md .gitignore docs
git commit -m "docs: define OCR labeling MVP"
git remote add origin https://github.com/YOUR-ORG/YOUR-REPO.git
git push -u origin main
```

If you prefer SSH and have a GitHub SSH key configured, use `git@github.com:YOUR-ORG/YOUR-REPO.git` as the remote URL. Confirm the remote with `git remote -v`.

### 5. Scaffold the stack in small steps

After agreeing on the stack, scaffold backend and frontend separately using official framework instructions. Commit each known-good step. For Django, the rough shape is:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install django djangorestframework pillow
django-admin startproject config .
python manage.py startapp datasets
python manage.py startapp annotations
```

Pin dependencies in the project's chosen dependency file after installation. These commands do not yet create a production-ready service or configure PostgreSQL; local SQLite is enough for an initial learning prototype. Add a frontend scaffold only once the team chooses the frontend toolchain. Do not run every command blindly: confirm the versions and setup instructions for your environment, then write the verified steps into README.

### 6. First implementation issues

Create one issue per vertical slice:

1. Define OCR annotation examples and import contract.
2. Create database models and migrations for dataset, image, and OCR region.
3. Implement and fixture-test geometry validation.
4. Implement safe ZIP inspection and dry-run import report.
5. Implement dataset/image API and API tests.
6. Build image display and rectangle drawing with transcription editing.
7. Implement save/reload and concurrency conflict behavior.
8. Implement export and a round-trip fixture test.
9. Add CI and an end-to-end smoke test.

The first demo should complete one complete path with a tiny synthetic dataset. Add more features only after this path is reliable.

## Definition of done for the MVP

- A teammate can clone the repository and follow the README to run the app and tests.
- A valid sample archive imports; invalid archives produce understandable errors and do not leave partial datasets.
- An annotator can create/edit/save OCR regions and Unicode transcriptions, then reload them accurately.
- A second user cannot silently overwrite newer annotation changes.
- Export output matches a checked-in synthetic expected fixture.
- CI runs on proposed changes, and at least one human reviews each merge.
- The group can explain the architecture and the data flow without relying on an AI tool.
