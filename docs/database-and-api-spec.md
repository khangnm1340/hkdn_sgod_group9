# OCR + Face Annotation Platform
## Database Schema and API Contract — v1 proposal

**Status:** Draft for team review  
**Stack:** React + TypeScript · Django + Django REST Framework · PostgreSQL · local file storage

This document defines the first implementation contract for the platform. It is intentionally a modular monolith: one Django backend, one React frontend, one PostgreSQL database, and one local media-storage volume. It does not require microservices or a task queue for the first milestone.

---

## 1. Scope and assumptions

### In scope for v1

- User authentication.
- Dataset creation and membership/permissions.
- Uploading and displaying images.
- Drawing rectangular OCR regions and face boxes.
- Saving, editing, deleting, and retrieving annotations.
- Basic annotation review (pending, approved, rejected).
- Importing a ZIP of images, optionally with existing annotations.
- Exporting a dataset with its images and annotations.

### Explicitly out of scope for v1

- Running OCR or face-detection machine-learning models.
- Polygon, brush, keypoint, or video annotation.
- Cloud object storage.
- Real-time collaborative drawing on the same image.
- Background workers and asynchronous import/export. Add these only if synchronous processing becomes too slow.

### Decisions to confirm before implementation

1. This proposal uses **rectangular bounding boxes** for both OCR and face annotations.
2. It proposes a small, versioned JSON format named `annotation-platform` for import/export. It is not COCO or ICDAR. Add a COCO/ICDAR adapter if the course dataset requires one.
3. OCR transcription may be an empty string while work is in progress. Face annotations have no transcription.
4. Dataset roles are `owner`, `annotator`, and `reviewer`.
5. New accounts may self-register in a closed/demo environment; disable public registration and provision accounts through an administrator for a restricted deployment.

---

## 2. Architecture boundaries

```text
React + TypeScript
  ├── Login / account screens
  ├── Dataset and member management
  ├── Image viewer and annotation editor
  └── API client
          │ HTTPS / JSON / multipart uploads
          ▼
Django + Django REST Framework
  ├── accounts       authentication and user profile
  ├── datasets       datasets, members, and images
  ├── annotations    OCR regions, face boxes, review state
  └── imports        ZIP validation, import, and export
          │                         │
          ▼                         ▼
PostgreSQL                    Local file storage
users, datasets,              original image files,
members, images,              staged ZIP files,
annotations, imports          generated exports
```

The database stores image metadata and file paths. It does **not** store image bytes. Keep uploaded files in `MEDIA_ROOT` on a persistent disk/volume, and keep that directory out of Git.

Suggested Django apps:

```text
backend/
├── config/
├── accounts/
├── datasets/
├── annotations/
└── imports/
```

---

## 3. Database schema

Use UUID primary keys for domain records so IDs are not tied to sequential database counters. Use Django's custom user model from the very first migration; changing `AUTH_USER_MODEL` after creating migrations is difficult.

### 3.1 User

Use a custom Django user model derived from `AbstractUser` with email as the login identifier.

| Field | Type | Rules / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `email` | Email, max 254 | Required, unique; login identifier |
| `password` | Django password field | Store only Django's password hash; never plaintext |
| `first_name` | varchar(150) | Optional |
| `last_name` | varchar(150) | Optional |
| `is_active` | boolean | Account enabled/disabled |
| `is_staff` | boolean | Django admin access; not the same as dataset owner |
| `date_joined` | datetime | Created timestamp |

Do not build a second password system. Use Django's built-in password hashing and authentication facilities.

### 3.2 Dataset

| Field | Type | Rules / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | varchar(150) | Required |
| `description` | text | Optional; blank allowed |
| `created_by_id` | FK → User | Original creator; protect from accidental deletion |
| `created_at` | datetime | Set automatically |
| `updated_at` | datetime | Updated automatically |

A dataset is the container for images and dataset membership. The creator is automatically added as an `owner` in `DatasetMembership` in the same database transaction that creates the dataset.

### 3.3 DatasetMembership

This joins users to datasets and defines what each user can do.

| Field | Type | Rules / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `dataset_id` | FK → Dataset | Cascade when dataset is deleted |
| `user_id` | FK → User | Cascade when account is deleted, subject to account-retention policy |
| `role` | varchar(20) | `owner`, `annotator`, or `reviewer` |
| `added_by_id` | FK → User | User who added this member; nullable for system-created membership |
| `created_at` | datetime | Membership creation time |

**Constraint:** unique `(dataset_id, user_id)`. Each dataset must retain at least one owner. Enforce that rule in the service/API layer when changing or deleting memberships.

Role permissions:

| Action | Owner | Annotator | Reviewer |
|---|:---:|:---:|:---:|
| View dataset and images | Yes | Yes | Yes |
| Upload/delete images | Yes | No | No |
| Add/remove members and change roles | Yes | No | No |
| Create annotations | Yes | Yes | No |
| Edit/delete pending annotations | Yes | Yes | No |
| Review (approve/reject) annotations | Yes | No | Yes |
| Delete dataset | Yes | No | No |
| Export dataset | Yes | Yes | Yes |

For v1, annotators may edit pending annotations in their dataset. Approved/rejected annotations are locked to annotators; an owner may correct them, which resets their review state to `pending`.

### 3.4 Image

| Field | Type | Rules / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `dataset_id` | FK → Dataset | Parent dataset |
| `file` | ImageField | Local storage path; not a database blob |
| `original_filename` | varchar(255) | Filename supplied by uploader |
| `width` | positive integer | Actual pixel width, read from the image |
| `height` | positive integer | Actual pixel height, read from the image |
| `mime_type` | varchar(100) | Verified content type, not blindly trusted from filename |
| `size_bytes` | positive bigint | File size |
| `sha256` | char(64) | Content checksum for integrity/deduplication |
| `uploaded_by_id` | FK → User | User who uploaded the image |
| `created_at` | datetime | Upload time |

Indexes: `(dataset_id, created_at)` and `(dataset_id, original_filename)`. The stored file path should use a generated UUID, not the raw user-supplied filename, for example `datasets/<dataset-uuid>/images/<image-uuid>.jpg`.

Only accept supported raster image formats selected by the team (for example JPEG and PNG). Verify the actual file contents, decode the image, enforce upload size/dimension limits, and calculate dimensions/checksum on the server.

### 3.5 Annotation

Use one `Annotation` table with a `kind` field instead of separate OCR and face tables. Both annotation types share the same geometry and lifecycle; the type-specific difference is the OCR transcription.

| Field | Type | Rules / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `image_id` | FK → Image | Image containing the region |
| `kind` | varchar(10) | `ocr` or `face` |
| `x1` | decimal(12,3) | Left coordinate in original-image pixels |
| `y1` | decimal(12,3) | Top coordinate in original-image pixels |
| `x2` | decimal(12,3) | Right coordinate in original-image pixels |
| `y2` | decimal(12,3) | Bottom coordinate in original-image pixels |
| `transcription` | text, nullable | OCR text; null for face; empty string allowed for unfinished OCR |
| `status` | varchar(10) | `pending`, `approved`, or `rejected`; default `pending` |
| `created_by_id` | FK → User | Original author |
| `updated_by_id` | FK → User | Most recent editor |
| `reviewed_by_id` | nullable FK → User | Reviewer, if reviewed |
| `reviewed_at` | nullable datetime | Review time |
| `review_comment` | text | Optional reviewer comment |
| `version` | positive integer | Starts at 1; increments on every successful edit/review update |
| `created_at` | datetime | Creation time |
| `updated_at` | datetime | Last update time |

Geometry convention:

- Origin `(0, 0)` is the top-left corner of the original image.
- `x1, y1` is the top-left of the box; `x2, y2` is the bottom-right.
- Require `0 <= x1 < x2 <= image.width` and `0 <= y1 < y2 <= image.height`.
- The frontend converts displayed canvas coordinates to original-image coordinates before sending the request. The backend repeats all validation.

Database check constraints should enforce non-negative `x1/y1`, `x2 > x1`, and `y2 > y1`. The serializer/service must enforce the upper bounds using the related image's width and height.

Type rules:

- `kind = ocr`: `transcription` must not be null; it may be `""` until transcribed.
- `kind = face`: `transcription` must be null.
- A change to geometry or transcription resets `status` to `pending` and clears reviewer fields.

Indexes: `(image_id, kind)`, `(image_id, status)`, and `(created_by_id, created_at)`.

### 3.6 ImportBatch

A small staging record makes the import preview/confirm workflow possible without creating half a dataset.

| Field | Type | Rules / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `uploaded_by_id` | FK → User | User who submitted the ZIP |
| `dataset_name` | varchar(150) | Proposed dataset name |
| `archive_file` | FileField | ZIP in temporary local staging storage |
| `status` | varchar(12) | `validated`, `failed`, or `imported` |
| `validation_report` | JSONB | Summary, errors, and warnings from validation |
| `dataset_id` | nullable FK → Dataset | Set after successful confirmation |
| `created_at` | datetime | Upload time |
| `expires_at` | datetime | When unused staged files may be cleaned up |

Do not create the Dataset/Image/Annotation records until the user confirms a successful validation report. Confirmation should run in a transaction and clean up staged files on success or expiry.

### 3.7 Relationships overview

```text
User 1 ───── * Dataset (created_by)
User * ───── * Dataset (through DatasetMembership)
Dataset 1 ── * Image
Image 1 ──── * Annotation
User 1 ───── * Annotation (created_by / updated_by / reviewed_by)
User 1 ───── * ImportBatch
ImportBatch 0..1 ── 1 Dataset (after import)
```

### 3.8 Delete behavior

- Deleting a dataset deletes its membership, image records, and annotation records.
- Deleting an image deletes its annotations.
- Removing a member does not delete the user's account or their historical annotations.
- Deleting database rows does not automatically guarantee local files are removed. Use an explicit service or cleanup job to remove corresponding media files safely.
- Prefer deactivating user accounts over deleting accounts that have authored annotations.

---

## 4. API conventions

### Base URL

All endpoints are under `/api/v1/`.

### Content types

- JSON requests/responses: `application/json`.
- Image uploads and ZIP uploads: `multipart/form-data`.
- Dataset exports: `application/zip` download.

### Authentication

Use JWT access and refresh tokens, for example with `djangorestframework-simplejwt`.

Send the access token on protected requests:

```http
Authorization: Bearer <access-token>
```

The frontend should keep access tokens in memory where practical and handle refresh/expiry centrally. Do not put tokens or secrets in source control. A cookie-based session design is also valid, but choose one approach and use it consistently; this contract assumes JWT.

### Common response rules

- IDs are UUID strings.
- Timestamps are ISO-8601 UTC strings.
- List endpoints are paginated.
- Return `201 Created` for successful creation, `200 OK` for successful reads/updates, and `204 No Content` for successful deletion.
- Return `401` when unauthenticated, `403` when authenticated but not permitted, `404` when the resource does not exist or is not visible to the user, `400` for invalid input, and `409` for a stale annotation version.

Paginated list shape:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": []
}
```

Error shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request contains invalid data.",
    "details": {
      "x2": ["Must be greater than x1."]
    }
  }
}
```

---

## 5. API endpoints

### 5.1 Authentication and current user

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `POST` | `/auth/register/` | Create account (disable if registration is restricted) | Public, if enabled |
| `POST` | `/auth/token/` | Login and obtain access/refresh tokens | Public |
| `POST` | `/auth/token/refresh/` | Obtain a new access token | Public with refresh token |
| `GET` | `/auth/me/` | Get current user profile | Authenticated |
| `PATCH` | `/auth/me/` | Update permitted profile fields | Authenticated |

Login request:

```json
{
  "email": "annotator@example.com",
  "password": "example-password"
}
```

Login response:

```json
{
  "access": "<access-token>",
  "refresh": "<refresh-token>"
}
```

Current-user response:

```json
{
  "id": "7d5d7774-1a89-4d1b-9c1e-5e54853eb1d6",
  "email": "annotator@example.com",
  "first_name": "Alex",
  "last_name": "Example"
}
```

Do not return password hashes or refresh tokens from `/auth/me/`.

### 5.2 Datasets

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/datasets/` | List datasets the user belongs to | Dataset member |
| `POST` | `/datasets/` | Create dataset | Authenticated |
| `GET` | `/datasets/{dataset_id}/` | Get dataset details | Dataset member |
| `PATCH` | `/datasets/{dataset_id}/` | Update name/description | Owner |
| `DELETE` | `/datasets/{dataset_id}/` | Delete dataset | Owner |

Create dataset request:

```json
{
  "name": "Street Sign OCR",
  "description": "Images for OCR and face-box annotation."
}
```

Create dataset response:

```json
{
  "id": "31f9b7a2-c7f1-4ac0-9ba4-3b4f51a87c20",
  "name": "Street Sign OCR",
  "description": "Images for OCR and face-box annotation.",
  "created_by": "7d5d7774-1a89-4d1b-9c1e-5e54853eb1d6",
  "created_at": "2026-11-15T10:00:00Z",
  "updated_at": "2026-11-15T10:00:00Z",
  "current_user_role": "owner",
  "image_count": 0
}
```

### 5.3 Dataset membership

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/datasets/{dataset_id}/members/` | List members | Dataset member |
| `POST` | `/datasets/{dataset_id}/members/` | Add an existing user to dataset | Owner |
| `PATCH` | `/datasets/{dataset_id}/members/{user_id}/` | Change member role | Owner |
| `DELETE` | `/datasets/{dataset_id}/members/{user_id}/` | Remove member | Owner |

Add member request:

```json
{
  "email": "reviewer@example.com",
  "role": "reviewer"
}
```

Member response:

```json
{
  "user_id": "b3bcf33e-26e5-4e5d-82b1-b039eb647a20",
  "email": "reviewer@example.com",
  "role": "reviewer",
  "created_at": "2026-11-15T10:10:00Z"
}
```

For v1, the user must already have an account before an owner can add them. Email invitations can be added later.

### 5.4 Images

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/datasets/{dataset_id}/images/` | List images in dataset | Dataset member |
| `POST` | `/datasets/{dataset_id}/images/` | Upload one or more images | Owner |
| `GET` | `/images/{image_id}/` | Get image metadata | Dataset member |
| `GET` | `/images/{image_id}/file/` | Retrieve image bytes | Dataset member |
| `DELETE` | `/images/{image_id}/` | Delete image and its annotations | Owner |

Upload uses multipart form data. A request may contain repeated `files` fields, one for each image. The server validates every file before saving it; return a clear per-file result if some uploads are rejected. For an atomic bulk upload, reject the entire request if any file is invalid.

Example image metadata response:

```json
{
  "id": "c59a1460-6e6b-4b68-8c04-e160d6d97285",
  "dataset_id": "31f9b7a2-c7f1-4ac0-9ba4-3b4f51a87c20",
  "filename": "street-001.jpg",
  "width": 1920,
  "height": 1080,
  "mime_type": "image/jpeg",
  "size_bytes": 283104,
  "annotation_count": 0,
  "created_at": "2026-11-15T10:20:00Z"
}
```

Do not expose an unrestricted filesystem path. Serve private image files through a permission-checked endpoint or another authenticated media mechanism.

### 5.5 Annotations

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/images/{image_id}/annotations/` | List annotations for an image | Dataset member |
| `POST` | `/images/{image_id}/annotations/` | Create OCR or face annotation | Owner or annotator |
| `GET` | `/annotations/{annotation_id}/` | Get one annotation | Dataset member |
| `PATCH` | `/annotations/{annotation_id}/` | Edit geometry/transcription | Owner or annotator, subject to review lock |
| `DELETE` | `/annotations/{annotation_id}/` | Delete annotation | Owner or annotator, subject to review lock |
| `POST` | `/annotations/{annotation_id}/review/` | Approve or reject annotation | Owner or reviewer |

Optional list filters: `?kind=ocr`, `?kind=face`, `?status=pending`.

Create OCR annotation:

```json
{
  "kind": "ocr",
  "geometry": {
    "x1": 100,
    "y1": 50,
    "x2": 300,
    "y2": 120
  },
  "transcription": "Hello world"
}
```

Create face annotation:

```json
{
  "kind": "face",
  "geometry": {
    "x1": 340,
    "y1": 80,
    "x2": 430,
    "y2": 210
  }
}
```

Annotation response:

```json
{
  "id": "88ec3109-45b1-4aa8-a8ec-054bc76bf938",
  "image_id": "c59a1460-6e6b-4b68-8c04-e160d6d97285",
  "kind": "ocr",
  "geometry": {
    "x1": 100,
    "y1": 50,
    "x2": 300,
    "y2": 120
  },
  "transcription": "Hello world",
  "status": "pending",
  "version": 1,
  "created_by": "7d5d7774-1a89-4d1b-9c1e-5e54853eb1d6",
  "updated_by": "7d5d7774-1a89-4d1b-9c1e-5e54853eb1d6",
  "reviewed_by": null,
  "reviewed_at": null,
  "review_comment": "",
  "created_at": "2026-11-15T10:30:00Z",
  "updated_at": "2026-11-15T10:30:00Z"
}
```

Update request must include the version the client last read:

```json
{
  "version": 1,
  "geometry": {
    "x1": 105,
    "y1": 50,
    "x2": 305,
    "y2": 120
  },
  "transcription": "Hello, world"
}
```

On success, the server saves the change and returns `version: 2`. If the stored version is no longer `1`, return `409 Conflict` and do not overwrite the newer annotation:

```json
{
  "error": {
    "code": "stale_version",
    "message": "This annotation was changed by someone else. Reload it before saving."
  }
}
```

Review request:

```json
{
  "version": 2,
  "decision": "approved",
  "comment": "Transcription and region are correct."
}
```

`decision` must be `approved` or `rejected`. A successful review increments `version`, sets `reviewed_by` and `reviewed_at`, and saves the comment. If an owner/annotator later changes the annotation, the review state returns to `pending` and review fields are cleared.

### 5.6 Import

Use a two-step validate-then-confirm process so malformed ZIP files do not create partially imported datasets.

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `POST` | `/imports/validate/` | Upload ZIP and return validation report | Authenticated |
| `GET` | `/imports/{import_id}/` | Retrieve validation status/report | Uploader |
| `POST` | `/imports/{import_id}/confirm/` | Create dataset from validated import | Uploader |

`POST /imports/validate/` uses multipart form data:

- `file`: ZIP archive.
- `dataset_name`: requested dataset name.

Proposed ZIP layout:

```text
my-dataset.zip
├── images/
│   ├── image-001.jpg
│   └── image-002.jpg
└── annotations.json   # optional
```

If `annotations.json` is included, it uses the versioned format in section 6. The server must inspect ZIP entries safely and reject path traversal, suspicious expansion ratios, unsupported files, duplicate paths, and archives that exceed configured size/file-count limits. Verify file contents rather than trusting extensions.

Validation response:

```json
{
  "import_id": "35d81b6d-74f9-429b-94b2-98c9a4caa6e4",
  "status": "validated",
  "summary": {
    "images_found": 2,
    "annotations_found": 3,
    "ocr_regions": 2,
    "face_regions": 1,
    "errors_count": 0,
    "warnings_count": 0
  },
  "errors": [],
  "warnings": [],
  "expires_at": "2026-11-16T10:00:00Z"
}
```

If invalid, return `status: "failed"` with actionable errors, for example a missing image referenced by an annotation or a box outside image boundaries. Confirmation is allowed only for a successfully validated batch. The confirmation endpoint returns the created dataset and its image count.

### 5.7 Export

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/datasets/{dataset_id}/export/` | Download dataset ZIP | Dataset member |

For v1, export synchronously and return `application/zip`. Include all original images and one `annotations.json` file using the format in section 6. Add a configured size limit; introduce background export jobs only if real usage requires them.

---

## 6. Canonical import/export JSON format

This is the application's own versioned interchange format. Keeping it explicit allows the backend to support COCO or ICDAR later through separate import/export adapters without changing the internal database model.

Example `annotations.json`:

```json
{
  "format": "annotation-platform",
  "version": 1,
  "images": [
    {
      "file_name": "images/image-001.jpg",
      "width": 1920,
      "height": 1080
    }
  ],
  "annotations": [
    {
      "id": "annotation-001",
      "image_file_name": "images/image-001.jpg",
      "kind": "ocr",
      "bbox": [100, 50, 200, 70],
      "transcription": "Hello world"
    },
    {
      "id": "annotation-002",
      "image_file_name": "images/image-001.jpg",
      "kind": "face",
      "bbox": [340, 80, 90, 130]
    }
  ]
}
```

In this format, `bbox` is `[x, y, width, height]` in original-image pixels. Convert it to database/API geometry as `x1=x`, `y1=y`, `x2=x+width`, `y2=y+height`. OCR annotations require a `transcription` string; face annotations must omit it. Image dimensions should be checked against the actual decoded image.

Export ZIP layout:

```text
<dataset-name>.zip
├── images/
│   ├── <image-id>_image-001.jpg
│   └── <image-id>_image-002.jpg
└── annotations.json
```

Use a unique image ID in exported filenames to avoid collisions when different uploaded files share the same original filename.

---

## 7. Validation and security requirements

These requirements are part of the contract, not optional frontend behavior:

1. Every dataset/image/annotation endpoint checks the requesting user's dataset membership and role.
2. The server validates bounding boxes against the actual image width and height.
3. Uploaded files are size-limited, content-checked, decoded, and stored under generated names.
4. ZIP extraction must prevent path traversal and archive expansion abuse. Never blindly extract untrusted paths.
5. Do not expose local media paths or allow arbitrary filesystem path access.
6. Use Django's password hashing; never store plaintext passwords.
7. Configure CORS to the known frontend origin(s), not `*` with credentials.
8. Keep `SECRET_KEY`, database credentials, and deployment secrets in environment variables; do not commit `.env` files.
9. Use database transactions for dataset creation plus owner membership, import confirmation, and annotation updates.
10. Use optimistic version checks to prevent one annotator silently overwriting another annotator's changes.
11. Keep private or real face images out of Git and use synthetic fixtures for tests unless the team has explicit permission to use the data.

---

## 8. Minimum acceptance tests

### Accounts and permissions

- A user can log in and retrieve their profile.
- A user cannot list or retrieve a dataset they do not belong to.
- An annotator cannot add members, delete a dataset, or delete images.
- A reviewer can review annotations but cannot change their geometry.
- A dataset cannot be left without an owner.

### Images and annotations

- An owner can upload a valid image and retrieve its metadata/file.
- A non-image file renamed to `.jpg` is rejected.
- An OCR annotation can be created with a Unicode transcription.
- A face annotation can be created without a transcription.
- An OCR annotation with null transcription and a face annotation with a transcription are rejected.
- Coordinates outside image boundaries are rejected.
- An annotation can be edited, saved, and retrieved with the new values.
- A stale version returns `409 Conflict` and does not overwrite newer data.
- Editing a reviewed annotation resets its review state to `pending`.

### Import/export

- A valid ZIP imports images and optional annotations correctly.
- Invalid ZIP paths, unsupported files, missing referenced images, and invalid boxes produce clear validation errors.
- A failed import does not create a partial dataset.
- Exported ZIP contains all images and annotations.
- Importing an exported ZIP reproduces the same annotation geometry and transcription (round-trip test).

---

## 9. Suggested implementation order

Implement one complete vertical slice at a time:

1. Create the custom User model and run the initial migrations.
2. Create Dataset and DatasetMembership; implement dataset CRUD and role checks.
3. Implement image upload, metadata extraction, and permission-checked image retrieval.
4. Implement Annotation model, serializer validation, CRUD endpoints, and version conflict handling.
5. Build the React image editor against the agreed annotation request/response format.
6. Implement review actions.
7. Implement ZIP validation, confirmation, and export.
8. Add CI and the acceptance tests above.

Do not build OCR/face model inference, microservices, Kubernetes, or background workers before this workflow works reliably.

