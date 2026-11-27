import { Link, Outlet } from 'react-router-dom';

export function MainLayout() {
  return (
    <div>
      <nav>
        <Link to="/">Overview</Link> |{' '}
        <Link to="/projects">Projects</Link> |{' '}
        <Link to="/jobs">Jobs</Link> |{' '}
        <Link to="/profile">Profile Settings</Link> |{' '}
        <Link to="/login">Logout</Link>
      </nav>
      <hr />
      <Outlet />
    </div>
  );
}
