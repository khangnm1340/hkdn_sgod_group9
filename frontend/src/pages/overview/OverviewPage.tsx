import { Link } from 'react-router-dom';

export function OverviewPage() {
  return (
    <div>
      <div>OverviewPage</div>
      <Link to="/login">Login</Link> | <Link to="/register">Create Account</Link>
    </div>
  );
}
