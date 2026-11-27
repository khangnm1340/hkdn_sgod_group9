import { Outlet } from 'react-router-dom';

/**
 * Tạm mở tự do mọi URL trong giai đoạn setup trang trắng.
 * Khi nối API JWT thật, bật lại kiểm tra `useAuth().isAuthenticated` để chuyển hướng về `/login`.
 */
export function ProtectedRoute() {
  return <Outlet />;
}

/**
 * Tạm mở tự do mọi URL trong giai đoạn setup trang trắng.
 * Khi nối API JWT thật, bật lại kiểm tra `useAuth().isAuthenticated` để chuyển hướng về `/projects`.
 */
export function PublicOnlyRoute() {
  return <Outlet />;
}
