import { Link } from 'react-router-dom';

export function CreateAccountPage() {
  return (
    <div>
      <div>CreateAccountPage</div>
      <Link to="/projects">Sign Up</Link> | <Link to="/login">Sign In</Link>
    </div>
  );
}
