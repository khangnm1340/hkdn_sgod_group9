import { Link } from 'react-router-dom';
import { useAuth } from '../lib/auth-context';

const DEV_LINKS = [
  { to: '/login', label: 'Login' },
  { to: '/register', label: 'Register' },
  { to: '/datasets', label: 'Datasets' },
  { to: '/datasets/1/images', label: 'Images' },
  { to: '/datasets/1/members', label: 'Members' },
  { to: '/datasets/1/settings', label: 'Settings' },
  { to: '/import', label: 'Import' },
  { to: '/export', label: 'Export' },
  { to: '/profile', label: 'Profile' },
  { to: '/datasets/1/images/1/annotate', label: 'Editor' },
];

export function DevAuthBar() {
  const { user, isAuthenticated, login, logout } = useAuth();

  if (!import.meta.env.DEV) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 12px',
        background: '#111827',
        color: '#f9fafb',
        fontSize: '12px',
        zIndex: 9999,
      }}
    >
      <strong>DEV</strong>
      <span>{isAuthenticated ? `Signed in: ${user?.email}` : 'Signed out'}</span>
      {isAuthenticated ? (
        <button type="button" onClick={logout}>
          Logout
        </button>
      ) : (
        <button type="button" onClick={() => void login('dev@example.com', 'dev')}>
          Mock Login
        </button>
      )}
      <span style={{ opacity: 0.4 }}>|</span>
      {DEV_LINKS.map((link) => (
        <Link key={link.to} to={link.to} style={{ color: '#93c5fd' }}>
          {link.label}
        </Link>
      ))}
    </div>
  );
}
