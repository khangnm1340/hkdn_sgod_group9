# Kế Hoạch Triển Khai Module Authentication & Authorization (Phiên bản v2 - Tập Trung Backend & Swagger UI)

Tài liệu kế hoạch này đã được tinh chỉnh nhằm tập trung tối đa vào mục tiêu trọng tâm hiện tại: hoàn thiện toàn bộ các API Backend phục vụ hệ thống Authentication & Authorization và đảm bảo khả năng vận hành, kiểm thử tương tác 100% trên giao diện Swagger UI (OpenAPI 3.0). Các công việc tích hợp giao diện Frontend (React/TypeScript) được chuyển sang giai đoạn tiếp theo.

---

## 1. Tổng Quan Kiến Trúc & Mục Tiêu Hiện Tại

Hệ thống SGOD (OCR & Face Annotation Platform) được thiết kế theo kiến trúc **Modular Monolith**, kết hợp giữa Backend Django REST Framework (DRF) và ứng dụng Frontend React/TypeScript. Phân hệ Authentication là bước nền tảng quyết định độ tin cậy và khả năng phân quyền toàn hệ thống.

### 1.1. Phạm Vi & Mục Tiêu Trọng Tâm (Backend & Swagger Focus)
- **Mục tiêu ưu tiên số 1**: Hoàn thiện toàn bộ logic xử lý phía Backend cho 7 endpoints xác thực core và 11 Yêu cầu Chức năng (FR-01 đến FR-11).
- **Trọng tâm nghiệm thu**: Hệ thống Backend có khả năng tự động sinh tài liệu OpenAPI 3.0 schema qua `drf-spectacular` và cho phép đội ngũ phát triển kiểm thử trực tiếp mọi API (Đăng ký, Đăng nhập JWT, Refresh Token, Profile `/auth/me/`, Đổi mật khẩu, Đăng xuất) trên giao diện **Swagger UI** tại đường dẫn `/api/v1/schema/swagger-ui/`.
- **Điều chỉnh phạm vi**: Công việc nối API Client phía Frontend (`auth-context.tsx`, Auth Guards, giao diện UI React) sẽ tạm thời đóng vai trò là Giai đoạn 2 (Future Scope) sau khi Backend API đạt tiêu chuẩn nghiệm thu trên Swagger.

### 1.2. Các Khuyết Điểm Kiến Trúc Cần Xử Lý Ngay
Để đảm bảo Backend chạy ổn định và kết nối đúng cơ sở dữ liệu PostgreSQL qua Podman/Docker, hệ thống bắt buộc phải dọn dẹp các tồn tại kỹ thuật sau:

1. **Khắc phục cấu hình bị ghi đè trong `backend/config/settings.py`**:
   Các dòng 25–36 trong `settings.py` đọc cấu hình `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` và `DATABASES` từ tệp `.env`. Tuy nhiên các dòng 43–48 và 110–115 lại ghi đè cấu hình về SQLite3 và host rỗng. Cần xóa bỏ khối ghi đè để Django kết nối chính xác tới PostgreSQL 17 (`compose.yaml`).
2. **Chuẩn hóa kiểu khóa chính User sang UUIDv4**:
   Migration ban đầu `accounts/migrations/0001_initial.py` khởi tạo `User.id` dưới dạng `BigAutoField` (số nguyên tự tăng). Điều này vi phạm quy định thiết kế hệ thống (dùng `UUIDv4` cho toàn bộ các entity domain). Cần sửa model `accounts.User` và tạo lại migration từ đầu.
3. **Cài đặt package JWT & Swagger Schema**:
   Bổ sung gói `djangorestframework-simplejwt` để sinh và quản lý Token JWT, cùng `drf-spectacular` để cấu hình OpenAPI 3.0 Schema Auto-generation.
4. **Khắc phục sai lệch thông tin trong `.env.example`**:
   Điều chỉnh chuỗi mật khẩu `POSTGRES_PASSWORD=1234` trong `.env.example` cho khớp với `DATABASE_URL` (`local-dev-change-this`).
5. **Thiết lập Automated Test Suite**:
   Sử dụng `pytest-django` để viết unit tests và integration tests cho toàn bộ endpoints API trong app `accounts`.

---

## 2. Đặc Tả Yêu Cầu Chức Năng Backend (Functional Requirements - FR)

Bảng tổng hợp 11 Yêu cầu Chức năng cấu thành nên mô-đun Xác thực và Phân quyền Backend. Việc phân định rõ giữa vai trò Khách, Người dùng đã xác thực và Quản trị viên giúp Backend xây dựng các lớp Permission Classes chính xác:

| Mã FR | Nhóm Chức Năng | Tên Chức Năng | Mô Tả Kỹ Thuật Phía Backend | Quyền Truy Cập (Backend Class) |
| :--- | :--- | :--- | :--- | :--- |
| **FR-01** | Đăng ký & Đăng nhập | Đăng ký tài khoản mới | Endpoint `/api/v1/auth/register/` nhận Email, Password, Họ tên. Mã hóa mật khẩu PBKDF2, sinh khóa chính UUIDv4 và kiểm tra trùng email. | Public (`AllowAny`) |
| **FR-02** | Đăng ký & Đăng nhập | Đăng nhập hệ thống | Endpoint `/api/v1/auth/token/` kiểm tra Email & Mật khẩu. Sinh cặp JWT Token (Access Token & Refresh Token) và trả về thông tin User. | Public (`AllowAny`) |
| **FR-03** | Đăng ký & Đăng nhập | Đăng xuất | Endpoint `/api/v1/auth/logout/` nhận Refresh Token và đưa vào danh sách đen (`token_blacklist_blacklistedtoken`). | Authenticated (`IsAuthenticated`) |
| **FR-04** | Quản lý Token | Làm mới Access Token | Endpoint `/api/v1/auth/token/refresh/` kiểm tra Refresh Token hợp lệ và trả về Access Token mới. | Public (`AllowAny`) |
| **FR-05** | Quản lý Token | Bảo vệ đường dẫn API | Backend áp dụng Middleware xác thực JWT (`JWTAuthentication`) và từ chối yêu cầu không hợp lệ với mã HTTP 401 Unauthorized. | System Authorization |
| **FR-06** | Quản lý Token | Đính kèm Bearer Token | Backend yêu cầu Header `Authorization: Bearer <access_token>` đối với toàn bộ các API bảo mật. | System Protocol |
| **FR-07** | Hồ sơ & Tài khoản | Lấy thông tin cá nhân | Endpoint `GET /api/v1/auth/me/` trả về thông tin hồ sơ người dùng hiện tại (ID, Email, Họ tên) từ `request.user`. | Authenticated (`IsAuthenticated`) |
| **FR-08** | Hồ sơ & Tài khoản | Cập nhật hồ sơ cá nhân | Endpoint `PATCH /api/v1/auth/me/` cho phép cập nhật các trường `first_name` và `last_name`. | Authenticated (`IsAuthenticated`) |
| **FR-09** | Hồ sơ & Tài khoản | Đổi mật khẩu tài khoản | Endpoint `/api/v1/auth/change-password/` xác nhận mật khẩu cũ và băm mã hóa mật khẩu mới. | Authenticated (`IsAuthenticated`) |
| **FR-10** | Quản trị Hệ thống | Khởi tạo Superuser/Admin | Cung cấp khả năng tạo tài khoản Quản trị qua lệnh CLI `python manage.py createsuperuser` theo chuẩn CVAT. | System Admin CLI |
| **FR-11** | Phân quyền RBAC | Phân quyền theo Dataset | Backend đối chiếu vai trò người dùng trong bảng `DatasetMembership` (Owner, Annotator, Reviewer) để phân quyền API Dataset. | RBAC Permission Guard |

---

## 3. Ma Trận API Backend & Cấu Trúc Payloads Kiểm Thử Trên Swagger

Mọi API của phân hệ Xác thực Backend được định tuyến dưới tiền tố URI `/api/v1/auth/` và hỗ trợ đầy đủ OpenAPI Schema decorators (`@extend_schema`).

### 3.1. Ánh Xạ Kiến Trúc Xử Lý Phía Backend
Bảng dưới đây mô tả chi tiết sự tương quan giữa Endpoint, HTTP Method, Class View, Serializer và câu lệnh truy vấn PostgreSQL tương ứng:

| API Endpoint | Method | Class View (accounts/views.py) | Serializer (accounts/serializers.py) | Thao Tác PostgreSQL & Code Logic |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/register/` | `POST` | `RegisterView` | `RegisterSerializer` | `UserManager.create_user()` - `INSERT INTO accounts_user (id=UUID, password=PBKDF2)` |
| `/api/v1/auth/token/` | `POST` | `CustomTokenObtainPairView` | `CustomTokenObtainPairSerializer` | `authenticate()`, `RefreshToken.for_user()` - `SELECT * FROM accounts_user WHERE email = %s` |
| `/api/v1/auth/token/refresh/` | `POST` | `TokenRefreshView` | `TokenRefreshSerializer` | SimpleJWT Refresh Engine - `SELECT FROM token_blacklist_outstandingtoken` |
| `/api/v1/auth/logout/` | `POST` | `LogoutView` | `LogoutSerializer` | `RefreshToken.blacklist()` - `INSERT INTO token_blacklist_blacklistedtoken` |
| `/api/v1/auth/me/` | `GET` | `UserMeView` | `UserSerializer` | JWT Middleware verify -> `SELECT * FROM accounts_user WHERE id = %s` |
| `/api/v1/auth/me/` | `PATCH` | `UserMeView` | `UserUpdateSerializer` | Cập nhật họ tên -> `UPDATE accounts_user SET first_name = %s, last_name = %s` |
| `/api/v1/auth/change-password/` | `POST` | `ChangePasswordView` | `ChangePasswordSerializer` | Verify old password & rehash -> `UPDATE accounts_user SET password = %s` |

---

### 3.2. Cấu Trúc JSON Payloads Phục Vụ Kiểm Thử Trực Tiếp Trên Swagger UI

#### 3.2.1. Đăng ký tài khoản mới (`POST /api/v1/auth/register/`)
- **Header**: `Content-Type: application/json`

*Request Payload mẫu trên Swagger:*
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "Nguyen",
  "last_name": "Van A"
}
```

*Response 201 Created (Kịch bản thành công):*
```json
{
  "id": "e4a7c1b2-8f9d-4e12-b536-123456789abc",
  "email": "user@example.com",
  "first_name": "Nguyen",
  "last_name": "Van A",
  "message": "Đăng ký tài khoản thành công"
}
```

*Response 400 Bad Request (Kịch bản lỗi dữ liệu / Email trùng):*
```json
{
  "email": ["Email này đã được sử dụng trên hệ thống."],
  "password": ["Mật khẩu phải có độ dài tối thiểu 8 ký tự."]
}
```

---

#### 3.2.2. Đăng nhập hệ thống & Sinh JWT Token (`POST /api/v1/auth/token/`)
- **Header**: `Content-Type: application/json`

*Request Payload mẫu trên Swagger:*
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

*Response 200 OK (Kịch bản thành công):*
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "e4a7c1b2-8f9d-4e12-b536-123456789abc",
    "email": "user@example.com",
    "first_name": "Nguyen",
    "last_name": "Van A"
  }
}
```

*Response 401 Unauthorized (Kịch bản sai thông tin đăng nhập):*
```json
{
  "detail": "Email hoặc mật khẩu không chính xác."
}
```

---

#### 3.2.3. Làm mới Access Token (`POST /api/v1/auth/token/refresh/`)
- **Header**: `Content-Type: application/json`

*Request Payload mẫu trên Swagger:*
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

*Response 200 OK (Kịch bản thành công):*
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

#### 3.2.4. Đăng xuất & Vô hiệu hóa Token (`POST /api/v1/auth/logout/`)
- **Header**: `Authorization: Bearer <access_token>`, `Content-Type: application/json`

*Request Payload mẫu trên Swagger:*
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

*Response 200 OK (Kịch bản thành công):*
```json
{
  "detail": "Đăng xuất thành công."
}
```

---

#### 3.2.5. Xem & Cập nhật hồ sơ cá nhân (`GET` & `PATCH /api/v1/auth/me/`)
- **Header**: `Authorization: Bearer <access_token>`

*Response 200 OK cho `GET /api/v1/auth/me/`:*
```json
{
  "id": "e4a7c1b2-8f9d-4e12-b536-123456789abc",
  "email": "user@example.com",
  "first_name": "Nguyen",
  "last_name": "Van A",
  "is_active": true,
  "date_joined": "2026-11-26T08:00:00Z"
}
```

*Request Payload cho `PATCH /api/v1/auth/me/`:*
```json
{
  "first_name": "Nguyen Van",
  "last_name": "B"
}
```

---

#### 3.2.6. Đổi mật khẩu tài khoản (`POST /api/v1/auth/change-password/`)
- **Header**: `Authorization: Bearer <access_token>`

*Request Payload mẫu trên Swagger:*
```json
{
  "old_password": "SecurePassword123!",
  "new_password": "NewSecurePassword456!"
}
```

*Response 200 OK (Kịch bản thành công):*
```json
{
  "detail": "Đổi mật khẩu thành công."
}
```

---

## 4. Kế Hoạch Thực Thi Backend 5 Bước & Tích Hợp Swagger UI

Để đạt được mục tiêu hệ thống Backend vận hành hoàn chỉnh và nghiệm thu 100% các API trên Swagger UI, quy trình thực thi được cấu trúc lại thành 5 bước tập trung Backend duy nhất:

### Bước 1: Dọn Dẹp Cấu Hình Django & Cài Đặt Phụ Thuộc Backend
1. **Chỉnh sửa `backend/config/settings.py`**:
   - Xóa bỏ đoạn mã ghi đè SQLite3 ở các dòng 43–48 và 110–115.
   - Bổ sung cấu hình `REST_FRAMEWORK` chuẩn hóa:
     ```python
     REST_FRAMEWORK = {
         "DEFAULT_AUTHENTICATION_CLASSES": (
             "rest_framework_simplejwt.authentication.JWTAuthentication",
         ),
         "DEFAULT_PERMISSION_CLASSES": (
             "rest_framework.permissions.IsAuthenticated",
         ),
         "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
     }
     ```
   - Khai báo cấu hình `SIMPLE_JWT` (thời gian hiệu lực Access Token 15 phút, Refresh Token 7 ngày, bật `ROTATE_REFRESH_TOKENS` và `BLACKLIST_AFTER_ROTATION`).
   - Thêm `drf_spectacular` và `rest_framework_simplejwt.token_blacklist` vào `INSTALLED_APPS`.
   - Cấu hình `SPECTACULAR_SETTINGS` (Title: "SGOD Platform API", Version: "v1").
2. **Cài đặt thư viện Python**:
   Chạy lệnh cài đặt phụ thuộc qua `uv`:
   ```bash
   uv add djangorestframework-simplejwt drf-spectacular
   ```
3. **Đồng bộ môi trường `.env.example`**:
   Sửa lại giá trị mật khẩu `POSTGRES_PASSWORD` trùng khớp hoàn toàn với chuỗi `DATABASE_URL`.

---

### Bước 2: Tái Cấu Trúc Model User & Khởi Tạo Migration PostgreSQL
1. **Cập nhật `backend/accounts/models.py`**:
   - Khai báo model `User` kế thừa từ `AbstractUser`.
   - Gán `username = None`, thiết lập `email = models.EmailField(unique=True)`, và `USERNAME_FIELD = "email"`.
   - Thiết lập trường id dạng UUIDv4: `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`.
   - Triển khai `UserManager` kế thừa `BaseUserManager` ghi đè phương thức `create_user` và `create_superuser`.
2. **Khởi tạo lại Migration**:
   - Xóa tệp migration cũ `accounts/migrations/0001_initial.py`.
   - Chạy lệnh makemigrations và migrate để tạo bảng `accounts_user` trong PostgreSQL 17:
     ```bash
     uv run python manage.py makemigrations accounts
     uv run python manage.py migrate
     ```

---

### Bước 3: Đóng Gói Serializers, Views & Gắn OpenAPI Decorators
1. **Xây dựng `backend/accounts/serializers.py`**:
   - `RegisterSerializer`: Mã hóa mật khẩu PBKDF2 qua `create_user`, kiểm tra trùng lặp email.
   - `CustomTokenObtainPairSerializer`: Trả về cặp Token JWT kèm object thông tin User cơ bản.
   - `UserSerializer` & `UserUpdateSerializer`: Phục vụ truy xuất/cập nhật profile `/auth/me/`.
   - `ChangePasswordSerializer`: Kiểm tra mật khẩu cũ qua `user.check_password()` và lưu mật khẩu mới.
2. **Xây dựng `backend/accounts/views.py`**:
   - Triển khai các Class Views: `RegisterView`, `CustomTokenObtainPairView`, `UserMeView`, `ChangePasswordView`, và `LogoutView`.
   - Trực tiếp gắn decorator `@extend_schema` từ `drf-spectacular` lên các View method để tự động mô tả chi tiết Request Body, Query Parameters, Response Payloads (mã 200, 201, 400, 401) phục vụ Swagger UI.

---

### Bước 4: Định Tuyến URLs & Tích Hợp Swagger UI / ReDoc
1. **Tạo `backend/accounts/urls.py`**:
   Khai báo 7 tuyến đường xác thực dưới tiền tố `/api/v1/auth/`:
   ```python
   urlpatterns = [
       path("register/", RegisterView.as_view(), name="register"),
       path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
       path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
       path("logout/", LogoutView.as_view(), name="logout"),
       path("me/", UserMeView.as_view(), name="user_me"),
       path("change-password/", ChangePasswordView.as_view(), name="change_password"),
   ]
   ```
2. **Cấu hình `backend/config/urls.py`**:
   Nhúng các route của `accounts` và bổ sung các tuyến đường Swagger UI endpoint:
   ```python
   from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

   urlpatterns = [
       path("admin/", admin.site.urls),
       path("api/v1/auth/", include("accounts.urls")),
       path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
       path("api/v1/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
       path("api/v1/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
   ]
   ```

---

### Bước 5: Kiểm Thử Tự Động & Nghiệm Thu Trên Swagger UI
1. **Viết Test Suite (`pytest-django`)**:
   Tạo tệp `backend/accounts/tests/test_auth_api.py` sử dụng `pytest-django` để kiểm thử tự động toàn bộ 7 endpoints API (xác nhận mã phản hồi HTTP 201, 200, 400, 401). Chạy lệnh:
   ```bash
   uv run pytest
   ```
2. **Nghiệm thu tương tác trên Swagger UI**:
   - Mở trình duyệt tại địa chỉ: `http://localhost:8000/api/v1/schema/swagger-ui/`.
   - Thực hiện thao tác **"Try it out"** cho API `POST /api/v1/auth/register/` để đăng ký tài khoản mới.
   - Đăng nhập qua `POST /api/v1/auth/token/` để lấy chuỗi `access_token`.
   - Sử dụng nút **"Authorize"** ở góc trên Swagger UI, nhập chuỗi `Bearer <access_token>`.
   - Kiểm thử thực tế các API bảo mật (`GET /api/v1/auth/me/`, `PATCH /api/v1/auth/me/`, `POST /api/v1/auth/change-password/`, `POST /api/v1/auth/logout/`) trực tiếp từ giao diện Swagger UI.

---

## 6. Kế Hoạch Giai Đoạn 2 (Future Scope - Tích Hợp Frontend)

Sau khi hệ thống Backend Authentication được hoàn thiện và đạt tiêu chuẩn nghiệm thu 100% trên Swagger UI, các công việc phía Frontend sẽ được triển khai nối tiếp bao gồm:
1. **Cấu hình API Client**: Xây dựng Axios/Fetch Interceptor tự động gắn Bearer Access Token và xử lý làm mới Token khi gặp lỗi 401.
2. **Auth Context**: Nối `src/lib/auth-context.tsx` với API thật `/api/v1/auth/token/` và `/api/v1/auth/me/`.
3. **UI Layouts & Pages**: Hoàn thiện các trang `LoginPage`, `RegisterPage`, `ProfilePage` và các Auth Guards (`ProtectedRoute`, `PublicOnlyRoute`).
