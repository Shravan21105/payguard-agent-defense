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
  Flame,
  Menu,
  X,
  Zap,
} from 'lucide-react';
import { apiService } from '../services/api';
import { cn } from '../utils/cn';
import { ThemeToggle } from '../components/common/ThemeToggle';

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
  const [backendVersion, setBackendVersion] = useState<string>('1.0.0');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
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
      } catch {
        setBackendStatus('disconnected');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-800 dark:bg-navy-950 dark:text-navy-200 antialiased selection:bg-cyber-indigo selection:text-white transition-colors duration-200">
      {/* Ambient background glows */}
      <div className="fixed top-0 left-1/4 w-96 h-96 bg-blue-500/5 dark:bg-blue-600/10 rounded-full blur-[128px] pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-96 h-96 bg-violet-500/5 dark:bg-violet-600/10 rounded-full blur-[128px] pointer-events-none" />
      <div className="fixed top-1/2 right-10 w-64 h-64 bg-cyan-500/5 rounded-full blur-[96px] pointer-events-none" />

      {/* Sidebar Desktop */}
      <aside className="hidden lg:flex w-64 flex-shrink-0 bg-white/90 border-r border-slate-200/90 dark:bg-navy-900/90 dark:border-white/[0.08] backdrop-blur-xl flex-col justify-between select-none z-30 transition-colors duration-200">
        <div>
          {/* Logo Brand */}
          <div className="px-6 py-5 border-b border-slate-200/90 dark:border-white/[0.08] flex items-center gap-3 bg-slate-50/50 dark:bg-navy-900/40">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-600 shadow-primary-glow border border-white/20">
              <Shield className="w-5 h-5 text-white" />
              <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-400" />
              </span>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-base font-extrabold tracking-wider text-slate-900 dark:text-white">
                  PAYGUARD
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/10 dark:bg-indigo-500/20 border border-indigo-500/30 text-indigo-600 dark:text-cyan-300 font-semibold">
                  v{backendVersion}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-navy-400 font-mono tracking-tight">Agent Defense Layer</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-widest text-slate-400 dark:text-navy-400 font-semibold">
              Cybersecurity SOC
            </div>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={cn(
                    'group relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium font-sans transition-all duration-200',
                    isActive
                      ? 'bg-gradient-to-r from-blue-600/15 via-indigo-600/15 to-violet-600/10 text-indigo-700 dark:text-white border border-indigo-500/30 shadow-primary-glow font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 dark:text-navy-300 dark:hover:text-white dark:hover:bg-navy-800/60 hover:border-slate-200/50 dark:hover:border-white/5 border border-transparent'
                  )}
                >
                  <Icon
                    className={cn(
                      'w-4 h-4 transition-colors duration-200',
                      isActive ? 'text-cyber-indigo dark:text-cyber-cyan' : 'text-slate-400 dark:text-navy-400 group-hover:text-slate-800 dark:group-hover:text-white'
                    )}
                  />
                  <span className="tracking-wide">{item.name}</span>
                  {item.name === 'Live Monitoring' && (
                    <span className="ml-auto flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-cyan-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-400" />
                    </span>
                  )}
                  {isActive && (
                    <div className="absolute left-0 top-2 bottom-2 w-1 bg-gradient-to-b from-cyan-400 to-indigo-500 rounded-r" />
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer: System Status */}
        <div className="p-4 border-t border-slate-200/90 dark:border-white/[0.08] bg-slate-50/80 dark:bg-navy-900/80 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500 dark:text-navy-400 font-sans">Engine Status</span>
            <div className="flex items-center gap-1.5 font-mono text-[11px]">
              {backendStatus === 'connected' ? (
                <>
                  <span className="h-2 w-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />
                  <span className="text-emerald-600 dark:text-emerald-400 font-semibold tracking-wider">ONLINE</span>
                </>
              ) : backendStatus === 'checking' ? (
                <>
                  <span className="h-2 w-2 rounded-full bg-amber-500 dark:bg-amber-400 animate-pulse" />
                  <span className="text-amber-600 dark:text-amber-400 font-medium">CONNECTING</span>
                </>
              ) : (
                <>
                  <span className="h-2 w-2 rounded-full bg-rose-500 dark:bg-rose-400" />
                  <span className="text-rose-600 dark:text-rose-400 font-medium">OFFLINE</span>
                </>
              )}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-white dark:bg-navy-850/80 border border-slate-200 dark:border-white/[0.06] text-[11px] font-mono space-y-1.5 backdrop-blur-sm shadow-sm dark:shadow-none">
            <div className="flex items-center justify-between text-slate-500 dark:text-navy-400">
              <span>Network</span>
              <span className="text-blue-600 dark:text-cyber-cyan font-semibold">NEAR Testnet</span>
            </div>
            <div className="flex items-center justify-between text-slate-500 dark:text-navy-400">
              <span>Vault Contract</span>
              <span className="text-slate-800 dark:text-white font-mono text-[10px] truncate max-w-[110px]" title="payguard-vault.testnet">
                payguard-vault
              </span>
            </div>
            <div className="flex items-center justify-between text-slate-500 dark:text-navy-400">
              <span>Security Core</span>
              <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Ed25519 Native</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/60 dark:bg-navy-950/80 backdrop-blur-md lg:hidden flex"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div
            className="w-72 bg-white dark:bg-navy-900 border-r border-slate-200 dark:border-white/10 h-full p-4 flex flex-col justify-between"
            onClick={(e) => e.stopPropagation()}
          >
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-white/10">
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-cyber-indigo" />
                  <span className="font-mono font-bold text-slate-900 dark:text-white">PAYGUARD</span>
                </div>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 rounded text-slate-500 hover:text-slate-900 dark:text-navy-400 dark:hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <nav className="mt-4 space-y-1">
                {NAV_ITEMS.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium',
                        isActive
                          ? 'bg-cyber-indigo/15 text-indigo-700 dark:text-white border border-cyber-indigo/30'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-navy-300 dark:hover:text-white dark:hover:bg-navy-800'
                      )}
                    >
                      <Icon className="w-4 h-4 text-cyber-indigo dark:text-cyber-cyan" />
                      <span>{item.name}</span>
                    </NavLink>
                  );
                })}
              </nav>
            </div>
            <div className="pt-4 border-t border-slate-200 dark:border-white/10 flex justify-center">
              <ThemeToggle showLabel className="w-full justify-center" />
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
        {/* Top Header */}
        <header className="h-16 flex-shrink-0 bg-white/80 dark:bg-navy-900/70 border-b border-slate-200/90 dark:border-white/[0.08] backdrop-blur-xl px-4 sm:px-8 flex items-center justify-between z-20 transition-colors duration-200">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-navy-400 dark:hover:text-white dark:hover:bg-navy-800"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-gradient-to-r from-blue-600/10 via-indigo-600/10 to-cyan-500/10 dark:from-blue-600/20 dark:via-indigo-600/20 dark:to-cyan-500/20 border border-indigo-500/30 text-indigo-700 dark:text-white shadow-primary-glow">
                <Zap className="w-3.5 h-3.5 text-blue-600 dark:text-cyber-cyan" />
                <span>ACTIVE DEFENSE</span>
                <span className="hidden sm:inline text-slate-400 dark:text-navy-400">•</span>
                <span className="hidden sm:inline text-emerald-600 dark:text-emerald-400">DETERMINISTIC ENFORCEMENT</span>
              </span>
            </div>

            <span className="text-xs text-slate-500 dark:text-navy-400 hidden xl:inline font-mono">
              AI analyzes • Policy engine enforces • Smart contract protects
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-200 dark:border-white/[0.08] bg-slate-100/80 dark:bg-navy-800/80 text-xs font-mono text-slate-600 dark:text-navy-300">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-500 dark:bg-cyber-cyan animate-pulse" />
              <span>NEAR HACKATHON 2026</span>
            </div>

            {/* Global Theme Switcher */}
            <ThemeToggle />

            <NavLink
              to="/transactions"
              className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-500 hover:via-indigo-500 hover:to-violet-500 text-white text-xs font-semibold font-mono tracking-wider transition shadow-primary-glow border border-white/20 flex items-center gap-2 cursor-pointer active:scale-95"
            >
              <span>+ AUDIT TRANSACTION</span>
            </NavLink>
          </div>
        </header>

        {/* Page Content Viewport */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-8 bg-slate-50/60 dark:bg-navy-950/60 cyber-grid transition-colors duration-200">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
