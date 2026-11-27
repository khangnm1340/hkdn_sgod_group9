import { createBrowserRouter } from 'react-router-dom';
import { AuthLayout } from '../layouts/AuthLayout';
import { EditorLayout } from '../layouts/EditorLayout';
import { MainLayout } from '../layouts/MainLayout';
import { PublicLayout } from '../layouts/PublicLayout';
import { CreateAccountPage } from '../pages/auth/CreateAccountPage';
import { ForgotPasswordPage } from '../pages/auth/ForgotPasswordPage';
import { LoginPage } from '../pages/auth/LoginPage';
import { ProfileSettingsPage } from '../pages/auth/ProfileSettingsPage';
import { AnnotatorEditorPage } from '../pages/editor/AnnotatorEditorPage';
import { JobsManagementPage } from '../pages/jobs/JobsManagementPage';
import { JobViewPage } from '../pages/jobs/JobViewPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { OverviewPage } from '../pages/overview/OverviewPage';
import { ProjectsPage } from '../pages/projects/ProjectsPage';
import { ProtectedRoute, PublicOnlyRoute } from './guards';

export const router = createBrowserRouter([
  // 1. Public landing page
  {
    element: <PublicLayout />,
    children: [{ path: '/', element: <OverviewPage /> }],
  },

  // 2. Auth pages
  {
    element: <PublicOnlyRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: '/login', element: <LoginPage /> },
          { path: '/register', element: <CreateAccountPage /> },
          { path: '/forgot-password', element: <ForgotPasswordPage /> },
        ],
      },
    ],
  },

  // 3. Main workspace & Editor pages
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <MainLayout />,
        children: [
          { path: '/projects', element: <ProjectsPage /> },
          { path: '/jobs', element: <JobsManagementPage /> },
          { path: '/projects/:projectId/jobs', element: <JobsManagementPage /> },
          { path: '/projects/:projectId/jobs/:jobId', element: <JobViewPage /> },
          { path: '/profile', element: <ProfileSettingsPage /> },
        ],
      },
      {
        element: <EditorLayout />,
        children: [
          {
            path: '/projects/:projectId/jobs/:jobId/images/:imageId/annotate',
            element: <AnnotatorEditorPage />,
          },
        ],
      },
    ],
  },

  // 4. Fallback 404
  { path: '*', element: <NotFoundPage /> },
]);
