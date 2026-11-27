import { Link, useParams } from 'react-router-dom';

export function JobViewPage() {
  const { projectId = '1', jobId = '1' } = useParams();

  return (
    <div>
      <div>JobViewPage</div>
      <Link to={`/projects/${projectId}/jobs/${jobId}/images/1/annotate`}>Open Editor</Link> |{' '}
      <Link to={`/projects/${projectId}/jobs`}>Back to Jobs</Link>
    </div>
  );
}
