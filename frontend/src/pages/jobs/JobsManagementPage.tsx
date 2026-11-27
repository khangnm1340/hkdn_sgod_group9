import { Link, useParams } from 'react-router-dom';

export function JobsManagementPage() {
  const { projectId = '1' } = useParams();

  return (
    <div>
      <div>JobsManagementPage</div>
      <Link to={`/projects/${projectId}/jobs/1`}>Open Job #1</Link>
    </div>
  );
}
