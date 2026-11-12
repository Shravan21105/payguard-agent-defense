import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  Shield,
  Activity,
  ArrowRightLeft,
  Brain,
  Radio,
  FileCheck2,
  Sliders,
  Settings as SettingsIcon,
  CheckCircle2,
  Flame,
} from 'lucide-react';
import { apiService } from '../services/api';
import { cn } from '../utils/cn';

const NAV_ITEMS = [
  { name: 'Overview', path: '/', icon: Activity },
  { name: 'Live Monitoring', path: '/monitoring', icon: Radio },
  { name: 'Transactions', path: '/transactions', icon: ArrowRightLeft },
  { name: 'AI Security', path: '/ai-security', icon: Brain },
  { name: 'Threat Intelligence', path: '/threats', icon: Flame },
  { name: 'Approvals', path: '/approvals', icon: FileCheck2 },
  { name: 'Policies', path: '/policies', icon: Sliders },
  { name: 'Settings', path: '/settings', icon: SettingsIcon },
];

export const DashboardLayout: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [backendVersion, setBackendVersion] = useState<string>('0.1.0');
  const location = useLocation();

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await apiService.getHealth();
        if (res.status === 'healthy') {
          setBackendStatus('connected');
          setBackendVersion(res.version);
        } else {
          setBackendStatus('disconnected');
        }
      } catch (e) {
        setBackendStatus('disconnected');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-charcoal-950 text-charcoal-200">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-charcoal-900 border-r border-charcoal-800 flex flex-col justify-between select-none">
        <div>
          {/* Logo Brand */}
          <div className="px-6 py-5 border-b border-charcoal-800 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-forest-700 to-forest-900 border border-emerald-500/40 flex items-center justify-center shadow-shield-glow">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-base font-bold tracking-wider text-white">PAYGUARD</span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-forest-900 border border-emerald-600/30 text-emerald-400">
                  v{backendVersion}
                </span>
              </div>
              <p className="text-[11px] text-charcoal-400 font-mono">Agent Defense Layer</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            <div className="px-3 py-2 text-[11px] font-mono uppercase tracking-wider text-charcoal-400">
              Security Navigation
            </div>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                    isActive
                      ? 'bg-forest-900/60 text-emerald-300 border border-emerald-500/30 shadow-sm'
                      : 'text-charcoal-300 hover:text-white hover:bg-charcoal-850'
                  )}
                >
                  <Icon
                    className={cn(
                      'w-4 h-4 transition-colors',
                      isActive ? 'text-emerald-400' : 'text-charcoal-400'
                    )}
                  />
                  <span>{item.name}</span>
                  {item.name === 'Live Monitoring' && (
                    <span className="ml-auto flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer: System Status */}
        <div className="p-4 border-t border-charcoal-800 bg-charcoal-900/80 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-charcoal-400">Backend Engine</span>
            <div className="flex items-center gap-1.5 font-mono">
              {backendStatus === 'connected' ? (
                <>
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-emerald-400 font-medium">ONLINE</span>
                </>
              ) : backendStatus === 'checking' ? (
                <>
                  <span className="h-2 w-2 rounded-full bg-amber-400" />
                  <span className="text-amber-400">CHECKING</span>
                </>
              ) : (
                <>
                  <span className="h-2 w-2 rounded-full bg-rose-400" />
                  <span className="text-rose-400">OFFLINE</span>
                </>
              )}
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-charcoal-850 border border-charcoal-750 text-[11px] space-y-1">
            <div className="flex items-center justify-between text-charcoal-400">
              <span>Target Network</span>
              <span className="text-emerald-400 font-mono font-medium">NEAR Testnet</span>
            </div>
            <div className="flex items-center justify-between text-charcoal-400">
              <span>Policy Mode</span>
              <span className="text-white font-mono">Deterministic</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 flex-shrink-0 bg-charcoal-900 border-b border-charcoal-800 px-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-semibold bg-forest-900/80 border border-emerald-500/30 text-emerald-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                SHIELD ACTIVE • DETERMINISTIC ENFORCEMENT
              </span>
            </div>
            <span className="text-xs text-charcoal-400 hidden md:inline">
              AI analyzes • Policy engine enforces • Smart contract protects
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="px-3 py-1 rounded border border-charcoal-750 bg-charcoal-850 text-xs font-mono text-charcoal-300 flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              <span>NEAR HACKATHON 2026</span>
            </div>

            <NavLink
              to="/transactions"
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold font-mono tracking-wide transition shadow-sm flex items-center gap-1.5"
            >
              <span>+ ANALYZE TX</span>
            </NavLink>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-8 bg-charcoal-950">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
