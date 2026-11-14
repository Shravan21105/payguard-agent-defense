import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Overview } from './pages/Overview';

// Route-level code splitting for secondary pages
const LiveMonitoring = lazy(() => import('./pages/LiveMonitoring').then((m) => ({ default: m.LiveMonitoring })));
const Transactions = lazy(() => import('./pages/Transactions').then((m) => ({ default: m.Transactions })));
const AiSecurity = lazy(() => import('./pages/AiSecurity').then((m) => ({ default: m.AiSecurity })));
const ThreatIntelligence = lazy(() => import('./pages/ThreatIntelligence').then((m) => ({ default: m.ThreatIntelligence })));
const Approvals = lazy(() => import('./pages/Approvals').then((m) => ({ default: m.Approvals })));
const Policies = lazy(() => import('./pages/Policies').then((m) => ({ default: m.Policies })));
const Settings = lazy(() => import('./pages/Settings').then((m) => ({ default: m.Settings })));

const PageFallback: React.FC = () => (
  <div className="space-y-6 max-w-7xl mx-auto py-10 animate-pulse">
    <div className="h-28 rounded-2xl bg-slate-200/60 dark:bg-navy-800/60 border border-slate-200/80 dark:border-white/[0.08]" />
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="h-24 rounded-xl bg-slate-200/60 dark:bg-navy-800/60 border border-slate-200/80 dark:border-white/[0.08]" />
      <div className="h-24 rounded-xl bg-slate-200/60 dark:bg-navy-800/60 border border-slate-200/80 dark:border-white/[0.08]" />
      <div className="h-24 rounded-xl bg-slate-200/60 dark:bg-navy-800/60 border border-slate-200/80 dark:border-white/[0.08]" />
      <div className="h-24 rounded-xl bg-slate-200/60 dark:bg-navy-800/60 border border-slate-200/80 dark:border-white/[0.08]" />
    </div>
    <div className="h-64 rounded-2xl bg-slate-200/60 dark:bg-navy-800/60 border border-slate-200/80 dark:border-white/[0.08]" />
  </div>
);

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Overview />} />
            <Route
              path="monitoring"
              element={
                <Suspense fallback={<PageFallback />}>
                  <LiveMonitoring />
                </Suspense>
              }
            />
            <Route
              path="transactions"
              element={
                <Suspense fallback={<PageFallback />}>
                  <Transactions />
                </Suspense>
              }
            />
            <Route
              path="ai-security"
              element={
                <Suspense fallback={<PageFallback />}>
                  <AiSecurity />
                </Suspense>
              }
            />
            <Route
              path="threats"
              element={
                <Suspense fallback={<PageFallback />}>
                  <ThreatIntelligence />
                </Suspense>
              }
            />
            <Route
              path="approvals"
              element={
                <Suspense fallback={<PageFallback />}>
                  <Approvals />
                </Suspense>
              }
            />
            <Route
              path="policies"
              element={
                <Suspense fallback={<PageFallback />}>
                  <Policies />
                </Suspense>
              }
            />
            <Route
              path="settings"
              element={
                <Suspense fallback={<PageFallback />}>
                  <Settings />
                </Suspense>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
