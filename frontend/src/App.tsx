import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Overview } from './pages/Overview';
import { LiveMonitoring } from './pages/LiveMonitoring';
import { Transactions } from './pages/Transactions';
import { AiSecurity } from './pages/AiSecurity';
import { ThreatIntelligence } from './pages/ThreatIntelligence';
import { Approvals } from './pages/Approvals';
import { Policies } from './pages/Policies';
import { Settings } from './pages/Settings';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Overview />} />
          <Route path="monitoring" element={<LiveMonitoring />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="ai-security" element={<AiSecurity />} />
          <Route path="threats" element={<ThreatIntelligence />} />
          <Route path="approvals" element={<Approvals />} />
          <Route path="policies" element={<Policies />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
