# SGOD Platform - Backend Service

Dịch vụ Backend cho nền tảng SGOD (OCR & Face Annotation Platform), được xây dựng trên nền tảng **Django REST Framework (DRF)**, **PostgreSQL 17**, xác thực **JWT (SimpleJWT)** và tài liệu hóa tự động qua **Swagger UI (drf-spectacular)**.

---

## 1. Yêu Cầu Môi Trường (Prerequisites)

- **Python**: Phiên bản `>= 3.12`
- **Trình quản lý package**: [`uv`](https://docs.astral.sh/uv/)
- **Cơ sở dữ liệu**: **PostgreSQL 17** (đang chạy trên cổng `5432`)

---

## 2. Cài Đặt & Khởi Tạo Dự Án

### Bước 1: Thiết lập biến môi trường (.env)
Đảm bảo file `.env` ở thư mục gốc của dự án (`c:\hkdn_sgod_group9\.env`) đã có thông tin kết nối PostgreSQL:
```env
# PostgreSQL
POSTGRES_DB=annotation_platform
POSTGRES_USER=annotation_app
POSTGRES_PASSWORD=1234

# Django database connection
DATABASE_URL=postgres://annotation_app:1234@127.0.0.1:5432/annotation_platform

# Django core settings
DJANGO_SECRET_KEY=django-insecure-local-development-only
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### Bước 2: Cài đặt thư viện phụ thuộc
Di chuyển vào thư mục `backend/` và đồng bộ môi trường bằng `uv`:
```powershell
cd backend
uv sync
```

### Bước 3: Áp dụng Migrations vào Cơ sở dữ liệu
```powershell
uv run python manage.py migrate
```

### Bước 4 (Tùy chọn): Tạo tài khoản Quản trị (Superuser)
```powershell
uv run python manage.py createsuperuser
```

---

## 3. Khởi Chạy Backend Server

Khởi động server phát triển tại địa chỉ `127.0.0.1:8000`:
```powershell
uv run python manage.py runserver 127.0.0.1:8000
```

> **Lưu ý**: Dự án là Backend REST API nên truy cập đường dẫn gốc `http://127.0.0.1:8000/` sẽ trả về `404 Not Found`. Vui lòng truy cập các đường dẫn API và tài liệu bên dưới.

---

## 4. Danh Sách Đường Dẫn Quan Trọng (Endpoints & UI)

| Giao diện / Tính năng | Đường dẫn URL | Mô tả |
| :--- | :--- | :--- |
| **Swagger UI** | [http://127.0.0.1:8000/api/v1/schema/swagger-ui/](http://127.0.0.1:8000/api/v1/schema/swagger-ui/) | Giao diện kiểm thử trực quan và tài liệu tương tác API |
| **ReDoc** | [http://127.0.0.1:8000/api/v1/schema/redoc/](http://127.0.0.1:8000/api/v1/schema/redoc/) | Tài liệu API chuẩn OpenAPI 3.0 giao diện ReDoc |
| **OpenAPI Schema** | [http://127.0.0.1:8000/api/v1/schema/](http://127.0.0.1:8000/api/v1/schema/) | File tải OpenAPI JSON Schema |
| **Django Admin** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) | Trang quản trị hệ thống của Django |

---

## 5. Hướng Dẫn Kiểm Thử Tương Tác Trên Swagger UI

1. Mở trình duyệt truy cập: `http://127.0.0.1:8000/api/v1/schema/swagger-ui/`
2. **Đăng ký tài khoản mới**:
   - Chọn `POST /api/v1/auth/register/` -> Nhấn **Try it out** -> Nhập email, password, họ tên -> Nhấn **Execute**.
3. **Đăng nhập & Lấy Token**:
   - Chọn `POST /api/v1/auth/token/` -> Nhập email và password vừa tạo -> Nhấn **Execute**.
   - Sao chép chuỗi token trong trường `access`.
4. **Xác thực toàn bộ API bảo mật**:
   - Nhấn nút **Authorize** (biểu tượng ổ khóa màu xanh lá) ở góc phải trên cùng màn hình Swagger.
   - Nhập chuỗi theo định dạng: `Bearer <chuỗi_access_token>` -> Nhấn **Authorize** -> **Close**.
5. **Kiểm thử các API bảo mật**:
   - `GET /api/v1/auth/me/`: Xem hồ sơ cá nhân của tài khoản hiện tại.
   - `PATCH /api/v1/auth/me/`: Cập nhật `first_name` và `last_name`.
   - `POST /api/v1/auth/change-password/`: Đổi mật khẩu tài khoản.
   - `POST /api/v1/auth/logout/`: Đăng xuất và đưa `refresh_token` vào danh sách đen.

---

## 6. Chạy Kiểm Thử Tự Động (Automated Testing)

Dự án sử dụng `pytest-django` kết nối trực tiếp database PostgreSQL để kiểm thử 100% các luồng API:
```powershell
uv run python -m pytest
```
Hoặc chạy chi tiết từng test:
```powershell
uv run python -m pytest -v accounts/tests/test_auth_api.py
```
