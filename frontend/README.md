# Frontend — OCR + Face Annotation Platform

Ứng dụng React + TypeScript + Vite cho nền tảng gán nhãn OCR và Face Bounding Box.

## 1. Tech Stack & Lệnh chạy nhanh

- **Framework:** React 19 + TypeScript + Vite
- **Routing:** `react-router-dom` v7
- **Server State:** `@tanstack/react-query` v5
- **Canvas Editor:** `konva` + `react-konva`
- **Icons:** `lucide-react`
- **Linter:** `oxlint`

```bash
cd frontend
npm install
npm run dev      # Chạy dev server (mặc định http://localhost:5173)
npm run lint     # Kiểm tra lint bằng oxlint
npm run build    # Kiểm tra TypeScript (tsc -b) và build production
```

---

## 2. Cấu trúc thư mục (`src/`) & Ý nghĩa từng phần

```text
frontend/src/
├── main.tsx                    # Điểm vào (entry point), mount <App /> vào #root
├── App.tsx                     # Gốc ứng dụng: bọc <AppProviders> quanh <RouterProvider>
├── app/                        # Cấu hình cốt lõi của ứng dụng (routing, guard, provider)
│   ├── providers.tsx           # Bọc QueryClientProvider và AuthProvider cho toàn app
│   ├── router.tsx              # Khai báo toàn bộ cây route, layout và gắn guard
│   └── guards.tsx              # ProtectedRoute (chặn chưa login) & PublicOnlyRoute (chặn đã login)
├── lib/                        # Logic dùng chung, context, API client
│   └── auth-context.tsx        # Quản lý trạng thái đăng nhập (AuthProvider + hook useAuth)
├── components/                 # Component dùng chung nhiều nơi
│   └── DevAuthBar.tsx          # Thanh công cụ chỉ hiện khi dev: Mock Login/Logout & link test nhanh
├── layouts/                    # Khung bố cục bao bọc nhóm trang (dùng <Outlet />)
│   ├── AuthLayout.tsx          # Khung cho trang Login / Register
│   ├── DashboardLayout.tsx     # Khung chính cho Datasets, Import, Export, Profile
│   ├── DatasetDetailLayout.tsx # Khung lồng bên trong chi tiết 1 Dataset (tab Images / Members / Settings)
│   └── EditorLayout.tsx        # Khung toàn màn hình cho trình vẽ bounding box
└── pages/                      # Các màn hình cụ thể theo từng domain
    ├── auth/
    │   ├── LoginPage.tsx       # /login
    │   ├── RegisterPage.tsx    # /register
    │   └── ProfilePage.tsx     # /profile
    ├── datasets/
    │   ├── DatasetsPage.tsx        # /datasets
    │   ├── DatasetMembersPage.tsx  # /datasets/:datasetId/members
    │   └── DatasetSettingsPage.tsx # /datasets/:datasetId/settings
    ├── images/
    │   └── DatasetImagesPage.tsx   # /datasets/:datasetId/images
    ├── editor/
    │   └── AnnotatorEditorPage.tsx # /datasets/:datasetId/images/:imageId/annotate
    ├── imports/
    │   ├── ImportZipPage.tsx       # /import
    │   └── ImportReportPage.tsx    # /import/:importId
    ├── exports/
    │   └── ExportPage.tsx          # /export
    └── NotFoundPage.tsx            # * (404)
```

---

## 3. Luồng đi của ứng dụng (Application Flow)

### 3.1. Luồng khởi chạy (Bootstrapping)

```text
index.html (#root)
  └─▶ main.tsx
        └─▶ App.tsx
              └─▶ AppProviders (providers.tsx)
                    ├─ QueryClientProvider (TanStack Query)
                    └─ AuthProvider (lib/auth-context.tsx)
                          └─▶ RouterProvider (app/router.tsx)
                                └─▶ RootLayout (<Outlet /> + DevAuthBar khi DEV)
```

Mọi component nằm trong `RouterProvider` đều có thể gọi `useAuth()` để đọc thông tin người dùng hiện tại và gọi `useQuery`/`useMutation` của React Query.

### 3.2. Luồng điều hướng & Bảo vệ Route (Routing & Guards)

```text
Người dùng mở URL
  ├─ Thuộc nhóm Auth (/login, /register)
  │     └─▶ PublicOnlyRoute (guards.tsx)
  │           ├─ Đã đăng nhập ──▶ Redirect sang /datasets
  │           └─ Chưa đăng nhập ─▶ AuthLayout ─▶ LoginPage / RegisterPage
  │
  ├─ Thuộc nhóm App (/, /datasets, /import, /export, /profile, /.../annotate)
  │     └─▶ ProtectedRoute (guards.tsx)
  │           ├─ Chưa đăng nhập ─▶ Redirect sang /login (lưu lại location cũ trong state.from)
  │           └─ Đã đăng nhập ──▶ Layout tương ứng ─▶ Page tương ứng
  │                 ├─ /                  ──▶ tự redirect sang /datasets
  │                 └─ /datasets/:id      ──▶ tự redirect sang /datasets/:id/images
  │
  └─ Đường dẫn không khớp ──▶ NotFoundPage (*)
```

---

## 4. Trạng thái Auth hiện tại & Cách nối Backend thật sau này

Hiện tại khung Auth đã được nối sẵn hoàn chỉnh mà chưa cần đợi UI hay Backend:
- **`auth-context.tsx`** đang dùng mock auth trong bộ nhớ (`user` mặc định là `null`).
- **`DevAuthBar.tsx`** tự động hiển thị ở đáy màn hình khi chạy `npm run dev` (và tự biến mất khi `npm run build`), cho phép bấm **Mock Login / Logout** và nhảy nhanh qua mọi route để kiểm tra guard.

### Khi ghép UI và Backend thật (`/api/v1/auth/...`):
1. **Không cần sửa** `router.tsx`, `guards.tsx`, `providers.tsx` hay `App.tsx`.
2. Trong `src/lib/auth-context.tsx`:
   - Thay hàm `login(email, password)` bằng gọi `POST /api/v1/auth/token/` rồi `GET /api/v1/auth/me/`.
   - Thêm kiểm tra phiên đăng nhập ban đầu khi khởi động app (dùng `isLoading` để `guards.tsx` chờ trước khi redirect).
3. Trong `LoginPage.tsx` và `RegisterPage.tsx`: dựng form UI và gọi `const { login } = useAuth()`.
4. Xóa hoặc gỡ `DevAuthBar` khỏi `router.tsx` khi không còn cần test nhanh.
