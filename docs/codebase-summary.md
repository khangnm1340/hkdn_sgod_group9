# Codebase Summary — OCR + Face Annotation Platform

> **Mục đích:** Tổng hợp trạng thái hiện tại của codebase để làm nền tảng lên kế hoạch (plan) cho các tính năng tiếp theo.  
> **Branch hiện tại:** `Authentication` (commit mới nhất: `da03804 Add placeholder pages and route links`)

---

## 1. Tổng quan kiến trúc & Công nghệ

Dự án được thiết kế theo mô hình **Modular Monolith**:
- **Frontend:** React (`^19.3.1`) + TypeScript (`~7.0.2`) + Vite (`^8.3.6`)
  - Routing: `react-router-dom` (`^7.18.5`)
  - Data fetching: `@tanstack/react-query` (`^5.107.1`)
  - Canvas editor (đã cài sẵn): `konva` (`^10.9.1`), `react-konva` (`^19.3.2`)
  - Icons: `lucide-react` (`^1.77.0`)
  - Linter: `oxlint` (`^1.90.0`)
- **Backend:** Django (`>=6.1.3`) + Django REST Framework (`>=3.18.3`), quản lý bằng `uv` (Python `>=3.12`)
  - Packages đã cài (`backend/pyproject.toml`): `django`, `djangorestframework`, `django-cors-headers`, `django-environ`, `pillow`, `psycopg[binary]`, `pytest`, `pytest-django`, `ruff`.
  - Packages có trong tài liệu thiết kế nhưng **chưa cài**: `drf-spectacular`, package JWT (ví dụ `djangorestframework-simplejwt`).
- **Database & Storage:**
  - PostgreSQL 17 qua Docker/Podman (`compose.yaml`).
  - Local filesystem storage (`backend/media/`) cho ảnh upload, staging import và file export.

---

## 2. Cấu trúc thư mục hiện tại

```text
hkdn_sgod_group9/
├── AGENT.md                              # Quy tắc phát triển cho AI/team
├── README.md                             # Hướng dẫn setup, MVP scope, conventions
├── compose.yaml                          # PostgreSQL 17-alpine service
├── .env.example                          # Biến môi trường mẫu
├── docs/
│   ├── database-and-api-spec.md          # Spec DB & API v1 (canonical contract)
│   ├── ocr-labeling-mvp-architecture.md  # Tài liệu kiến trúc MVP
│   ├── jj_cheat_sheet.md                 # Ghi chú Jujutsu
│   ├── tasks.md                          # Ghi chú công việc
│   └── todo_list.md                      # Checklist tổng quát
├── backend/
│   ├── pyproject.toml & uv.lock          # Dependencies Python
│   ├── manage.py & main.py
│   ├── config/
│   │   ├── settings.py                   # Cấu hình Django
│   │   └── urls.py                       # Chỉ mới có /admin/
│   ├── accounts/                         # Custom User model + migration 0001
│   ├── datasets/                         # App rỗng (chưa có models/views/urls)
│   ├── annotations/                      # App rỗng (chưa có models/views/urls)
│   └── imports/                          # App rỗng (chưa có models/views/urls)
├── frontend/
│   ├── package.json & vite.config.ts
│   └── src/
│       ├── App.tsx & main.tsx
│       ├── app/
│       │   ├── providers.tsx             # QueryClientProvider + AuthProvider
│       │   ├── router.tsx                # Toàn bộ cây route + DevAuthBar
│       │   └── guards.tsx                # ProtectedRoute & PublicOnlyRoute
│       ├── lib/
│       │   └── auth-context.tsx          # Mock AuthProvider (in-memory)
│       ├── components/
│       │   └── DevAuthBar.tsx            # Thanh điều hướng nhanh khi DEV
│       ├── layouts/                      # 4 layouts (hiện chỉ render <Outlet />)
│       └── pages/                        # 12 placeholder pages
└── tests/
    └── fixtures/.gitkeep                 # Chưa có test fixtures
```

---

## 3. Chi tiết trạng thái Backend (`backend/`)

### 3.1. `config/`
- `settings.py`:
  - Đã khai báo `AUTH_USER_MODEL = "accounts.User"`.
  - Đã bật `INSTALLED_APPS`: `rest_framework`, `corsheaders`, `accounts`, `datasets`, `annotations`, `imports`.
  - Đã bật `CorsMiddleware` và `CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]`.
  - Đã cấu hình `MEDIA_URL = "/media/"` và `MEDIA_ROOT = BASE_DIR / "media"`.
- `urls.py`:
  - Hiện chỉ có `path('admin/', admin.site.urls)`. Chưa có route `/api/v1/` nào.

### 3.2. `accounts/` (Đã bắt đầu triển khai)
- `models.py`:
  - `User(AbstractUser)`: bỏ `username` (`username = None`), dùng `email` (`EmailField(unique=True)`) làm `USERNAME_FIELD`, `REQUIRED_FIELDS = []`.
  - `UserManager(BaseUserManager)`: cài đặt `create_user` và `create_superuser` theo `email`.
- `migrations/0001_initial.py`: đã tạo migration đầu tiên cho `accounts.User`.
- `views.py`, `admin.py`, `tests.py`: đang trống (mặc định của `startapp`).

### 3.3. `datasets/`, `annotations/`, `imports/`
- Cả 3 app mới chỉ được tạo bằng `startapp`: `models.py`, `views.py`, `admin.py`, `tests.py` đều chưa có code nghiệp vụ và chưa có migrations.

---

## 4. Chi tiết trạng thái Frontend (`frontend/`)

### 4.1. Kiến trúc ứng dụng & Auth giả lập
- `src/app/providers.tsx`: bọc `QueryClientProvider` (`@tanstack/react-query`) và `AuthProvider`.
- `src/lib/auth-context.tsx`: đang dùng **mock auth trong bộ nhớ** (`user` state mặc định `null`, `login()` gán cứng user `Dev User`, `logout()` set `null`). Có ghi chú thay bằng `POST /api/v1/auth/token/` + `GET /api/v1/auth/me/`.
- `src/app/guards.tsx`:
  - `ProtectedRoute`: chưa đăng nhập -> redirect `/login`.
  - `PublicOnlyRoute`: đã đăng nhập -> redirect `/datasets`.
- `src/components/DevAuthBar.tsx`: thanh công cụ nổi ở đáy màn hình trong môi trường `DEV`, cho phép Mock Login/Logout và nhảy nhanh tới tất cả các route.

### 4.2. Cây Route hiện tại (`src/app/router.tsx`)
- **Public-only (`AuthLayout`):**
  - `/login` -> `LoginPage`
  - `/register` -> `RegisterPage`
- **Protected (`DashboardLayout`):**
  - `/` -> redirect `/datasets`
  - `/datasets` -> `DatasetsPage`
  - `/datasets/:datasetId` (`DatasetDetailLayout`, index redirect sang `images`):
    - `/datasets/:datasetId/images` -> `DatasetImagesPage`
    - `/datasets/:datasetId/members` -> `DatasetMembersPage`
    - `/datasets/:datasetId/settings` -> `DatasetSettingsPage`
  - `/import` -> `ImportZipPage`
  - `/import/:importId` -> `ImportReportPage`
  - `/export` -> `ExportPage`
  - `/profile` -> `ProfilePage`
- **Protected (`EditorLayout`):**
  - `/datasets/:datasetId/images/:imageId/annotate` -> `AnnotatorEditorPage`
- **Fallback:** `*` -> `NotFoundPage`

### 4.3. Trạng thái Layouts & Pages
- Toàn bộ 4 layouts (`AuthLayout`, `DashboardLayout`, `DatasetDetailLayout`, `EditorLayout`) và 12 pages trong `src/pages/` hiện đang là **placeholder tối giản** (chỉ render `<Outlet />` hoặc stub).

---

## 5. Tài liệu đặc tả hiện có (`docs/`)

- [`docs/database-and-api-spec.md`](file:///c:/hkdn_sgod_group9/docs/database-and-api-spec.md): Đặc tả chi tiết schema v1 (`User`, `Dataset`, `DatasetMembership`, `Image`, `Annotation`, `ImportJob`), phân quyền theo vai trò (`owner`, `annotator`, `reviewer`), quy tắc tọa độ bounding box (`0 <= x1 < x2 <= width`, `0 <= y1 < y2 <= height`), optimistic locking (`version`), và hợp đồng API `/api/v1/`.
- [`docs/ocr-labeling-mvp-architecture.md`](file:///c:/hkdn_sgod_group9/docs/ocr-labeling-mvp-architecture.md): Tài liệu định hướng kiến trúc MVP, luồng import/export và save annotation.

---

## 6. Các vấn đề / khoảng trống cần xử lý trước khi code tính năng mới

1. **Cấu hình trùng lặp trong `backend/config/settings.py`:**
   - Dòng 25–36 đọc `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASES` từ `.env` (`DATABASE_URL`), nhưng ngay bên dưới (dòng 43–48 và 110–115) lại bị ghi đè bởi cấu hình mặc định của `startproject` (`sqlite3`, `ALLOWED_HOSTS = []`, `SECRET_KEY = 'django-insecure-...'`). Cần xóa phần ghi đè để Django thực sự dùng `.env` và PostgreSQL.
2. **Không khớp kiểu Primary Key của `User`:**
   - `accounts/migrations/0001_initial.py` đang tạo `User.id` kiểu `BigAutoField`, trong khi `docs/database-and-api-spec.md` quy định tất cả bảng domain dùng `UUID` làm Primary Key. Nên thống nhất sớm trước khi tạo các bảng có ForeignKey trỏ tới `User` (`Dataset`, `DatasetMembership`, `Annotation`, ...).
3. **Chưa có cấu hình DRF & Authentication backend:**
   - Chưa cấu hình `REST_FRAMEWORK` trong `settings.py`, chưa có package/endpoint đăng nhập (JWT hoặc Session/Token), đăng ký, `/me/`, và chưa có `config/urls.py` cho `/api/v1/`.
4. **Lệch thông tin mẫu trong `.env.example`:**
   - `POSTGRES_PASSWORD=1234` không khớp với mật khẩu trong `DATABASE_URL` (`local-dev-change-this`).
5. **Chưa có test suite:**
   - Tất cả `tests.py` và `tests/fixtures/` đều chưa có test thực tế.

---

## 7. Đề xuất thứ tự ưu tiên cho các bước plan tiếp theo

1. **Dọn nền tảng Backend:** Sửa `settings.py` (xóa block trùng lặp, cấu hình `REST_FRAMEWORK`), chốt kiểu `id` (`UUID` hay `BigAutoField`) cho `User`, sửa `.env.example`.
2. **Hoàn thiện slice `Authentication` (đang ở branch `Authentication`):**
   - Backend: cài/cấu hình auth (JWT hoặc session theo spec), endpoints `register`, `token`/`login`, `me`, `profile`, kèm unit/API tests.
   - Frontend: xây dựng `AuthLayout`, `LoginPage`, `RegisterPage`, `ProfilePage`, API client, và nối `auth-context.tsx` với backend thật.
3. **Triển khai các vertical slice tiếp theo theo `docs/database-and-api-spec.md`:**
   - `datasets` (Dataset, DatasetMembership, phân quyền `owner`/`annotator`/`reviewer`, upload & serve `Image`).
   - `annotations` (CRUD OCR/Face boxes, kiểm tra biên tọa độ, optimistic locking `version`, review state).
   - `imports` (ZIP validation preview + confirm import + export).
   - Frontend `DashboardLayout`, `DatasetDetailLayout`, và `AnnotatorEditorPage` với `react-konva`.
