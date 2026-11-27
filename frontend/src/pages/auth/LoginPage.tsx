import { Link } from 'react-router-dom';

export function LoginPage() {
  return (
    <div>
      <div>LoginPage</div>
      <Link to="/projects">Sign In</Link> |{' '}
      <Link to="/forgot-password">Forgot Password</Link> |{' '}
      <Link to="/register">Sign Up</Link> |{' '}
      <Link to="/">Overview</Link>
    </div>
  );
}
