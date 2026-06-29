import React from 'react';
import { useIsAuthenticated } from '@azure/msal-react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ZeroClawConsole from './pages/ZeroClawConsole';
import DocumentConsole from './pages/DocumentConsole';
import SupportPage from './pages/SupportPage';
import LegalPage from './pages/LegalPage';
import SuperAdminConsole from './pages/SuperAdminConsole';
import TenantAdminConsole from './pages/TenantAdminConsole';
import LoginPage from './components/auth/LoginPage';
import AppShell from './components/layout/AppShell';
import ChatContainer from './components/chat/ChatContainer';

import { useAuth } from './hooks/useAuth';

const App: React.FC = () => {
    const { isAuthenticated } = useAuth();

    if (!isAuthenticated) {
        return <LoginPage />;
    }

    return (
        <AppShell>
            <Routes>
                <Route path="/" element={<ChatContainer />} />
                <Route path="/internal/super-admin" element={<SuperAdminConsole />} />
                <Route path="/admin" element={<TenantAdminConsole />} />
                <Route path="/documents" element={<DocumentConsole />} />
                <Route path="/support" element={<SupportPage />} />
                <Route path="/agent/zeroclaw" element={<ZeroClawConsole />} />
                <Route path="/legal" element={<LegalPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </AppShell>
    );
};

export default App;
