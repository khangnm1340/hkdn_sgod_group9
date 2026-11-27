import { Link, Outlet, useParams } from 'react-router-dom';

export function EditorLayout() {
  const { projectId = '1', jobId = '1' } = useParams();

  return (
    <div>
      <nav>
        <Link to={`/projects/${projectId}/jobs/${jobId}`}>Back to Job View</Link>
      </nav>
      <hr />
      <Outlet />
    </div>
  );
}
