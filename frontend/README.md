# LABEL SPACE — Frontend Setup

Khung định tuyến (routing) ban đầu cho nền tảng **OCR + Face Annotation Platform**.  
Giai đoạn này chỉ nối luồng giữa các trang bằng trang trắng và `<Link>` thô — **chưa code UI và chưa nối API**.

---

## 1. Cấu trúc `frontend/src/`

```text
frontend/src/
├── main.tsx & App.tsx              # Khởi chạy ứng dụng (AppProviders + RouterProvider)
├── index.css & App.css             # Giữ nền trắng mặc định
├── app/
│   ├── router.tsx                  # Khai báo toàn bộ route
│   ├── providers.tsx               # React Query + AuthProvider
│   └── guards.tsx                  # ProtectedRoute & PublicOnlyRoute (đang mở tự do URL)
├── lib/
│   └── auth-context.tsx            # State đăng nhập (chờ nối JWT API)
├── components/
│   └── DevAuthBar.tsx              # Placeholder (trả về null)
├── layouts/
│   ├── PublicLayout.tsx            # Trang giới thiệu (/)
│   ├── AuthLayout.tsx              # Login, Create Account, Forgot Password
│   ├── MainLayout.tsx              # Thanh link chung (Overview, Projects, Jobs, Profile, Logout)
│   └── EditorLayout.tsx            # Link quay lại Job View + khung Editor
└── pages/
    ├── overview/OverviewPage.tsx
    ├── auth/                       # LoginPage, CreateAccountPage, ForgotPasswordPage, ProfileSettingsPage
    ├── projects/ProjectsPage.tsx
    ├── jobs/                       # JobsManagementPage, JobViewPage
    ├── editor/AnnotatorEditorPage.tsx
    └── NotFoundPage.tsx            # 404 (*)
```

---

## 2. Sơ đồ Route

| Route | Layout | Page |
|---|---|---|
| `/` | `PublicLayout` | `OverviewPage` |
| `/login` | `AuthLayout` | `LoginPage` |
| `/register` | `AuthLayout` | `CreateAccountPage` |
| `/forgot-password` | `AuthLayout` | `ForgotPasswordPage` |
| `/projects` | `MainLayout` | `ProjectsPage` |
| `/jobs` & `/projects/:projectId/jobs` | `MainLayout` | `JobsManagementPage` |
| `/projects/:projectId/jobs/:jobId` | `MainLayout` | `JobViewPage` |
| `/profile` | `MainLayout` | `ProfileSettingsPage` |
| `/projects/:projectId/jobs/:jobId/images/:imageId/annotate` | `EditorLayout` | `AnnotatorEditorPage` |
| `*` | — | `NotFoundPage` |

**Lưu ý:**
- `Logout` là nút hành động trong `MainLayout` (quay về `/login`), không tạo page riêng.
- Các popup (`Create Project`, `Create Job`, `Delete Image`) là Modal mở đè trên page tương ứng khi code UI, không tạo route riêng.

---

## 3. Cách chạy & kiểm tra luồng

```bash
npm --prefix frontend install   # Cài dependencies
npm --prefix frontend run dev   # Chạy local (mặc định http://localhost:5173)
npm --prefix frontend run build # Kiểm tra TypeScript & build
npm --prefix frontend run lint  # Kiểm tra lint (oxlint)
```

Mở `http://localhost:5173/` và bấm theo luồng:  
**`Overview` → `Login` → `Sign In` → `Projects` → `Open Jobs` → `Open Job #1` → `Open Editor` → `Back to Job View` → `Logout`**.

---

## 4. Bước tiếp theo

1. Code UI chi tiết cho các Layout, Page và Modal theo Figma `LABEL SPACE`.
2. Bật kiểm tra đăng nhập trong `src/app/guards.tsx` và nối API `/api/v1/` (Django DRF).
3. Xây dựng công cụ vẽ OCR / Face trên `react-konva`.
