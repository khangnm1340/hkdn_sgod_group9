import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { DevAuthBar } from '../components/DevAuthBar';
import { AuthLayout } from '../layouts/AuthLayout';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { DatasetDetailLayout } from '../layouts/DatasetDetailLayout';
import { EditorLayout } from '../layouts/EditorLayout';
import { LoginPage } from '../pages/auth/LoginPage';
import { RegisterPage } from '../pages/auth/RegisterPage';
import { ProfilePage } from '../pages/auth/ProfilePage';
import { DatasetsPage } from '../pages/datasets/DatasetsPage';
import { DatasetImagesPage } from '../pages/images/DatasetImagesPage';
import { DatasetMembersPage } from '../pages/datasets/DatasetMembersPage';
import { DatasetSettingsPage } from '../pages/datasets/DatasetSettingsPage';
import { ImportZipPage } from '../pages/imports/ImportZipPage';
import { ImportReportPage } from '../pages/imports/ImportReportPage';
import { ExportPage } from '../pages/exports/ExportPage';
import { AnnotatorEditorPage } from '../pages/editor/AnnotatorEditorPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { ProtectedRoute, PublicOnlyRoute } from './guards';

function RootLayout() {
    return (
        <>
            <Outlet />
            {import.meta.env.DEV && <DevAuthBar />}
        </>
    );
}

export const router = createBrowserRouter([
    {
        element: <RootLayout />,
        children: [
            {
                element: <PublicOnlyRoute />,
                children: [
                    {
                        element: <AuthLayout />,
                        children: [
                            { path: '/login', element: <LoginPage /> },
                            { path: '/register', element: <RegisterPage /> },
                        ],
                    },
                ],
            },
            {
                element: <ProtectedRoute />,
                children: [
                    {
                        element: <DashboardLayout />,
                        children: [
                            { index: true, element: <Navigate to="/datasets" replace /> },
                            { path: '/datasets', element: <DatasetsPage /> },
                            {
                                path: '/datasets/:datasetId',
                                element: <DatasetDetailLayout />,
                                children: [
                                    { index: true, element: <Navigate to="images" replace /> },
                                    { path: 'images', element: <DatasetImagesPage /> },
                                    { path: 'members', element: <DatasetMembersPage /> },
                                    { path: 'settings', element: <DatasetSettingsPage /> },
                                ],
                            },
                            { path: '/import', element: <ImportZipPage /> },
                            { path: '/import/:importId', element: <ImportReportPage /> },
                            { path: '/export', element: <ExportPage /> },
                            { path: '/profile', element: <ProfilePage /> },
                        ],
                    },
                    {
                        element: <EditorLayout />,
                        children: [
                            {
                                path: '/datasets/:datasetId/images/:imageId/annotate',
                                element: <AnnotatorEditorPage />,
                            },
                        ],
                    },
                ],
            },
            { path: '*', element: <NotFoundPage /> },
        ],
    },
]);