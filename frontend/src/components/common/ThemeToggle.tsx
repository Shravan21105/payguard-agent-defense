import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { cn } from '../../utils/cn';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  className,
  showLabel = false,
  size = 'md',
}) => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      type="button"
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Switch to ${isDark ? 'Light' : 'Cyber Dark'} Mode`}
      className={cn(
        'group relative inline-flex items-center gap-2 rounded-xl transition-all duration-300 select-none active:scale-95 cursor-pointer',
        'border border-slate-200/90 dark:border-white/[0.12]',
        'bg-white/80 dark:bg-navy-800/80 hover:bg-slate-100 dark:hover:bg-navy-750',
        'shadow-sm dark:shadow-glass-panel hover:shadow-primary-glow',
        'text-slate-700 dark:text-navy-200 hover:text-slate-900 dark:hover:text-white',
        size === 'sm' ? 'px-2.5 py-1.5 text-xs' : 'px-3 py-1.5 text-xs',
        className
      )}
    >
      <div className="relative flex items-center justify-center w-5 h-5">
        {/* Sun Icon for Light mode */}
        <Sun
          className={cn(
            'w-4 h-4 text-amber-500 transition-all duration-300 absolute',
            isDark
              ? 'opacity-0 rotate-90 scale-50 pointer-events-none'
              : 'opacity-100 rotate-0 scale-100'
          )}
        />
        {/* Moon Icon for Dark mode */}
        <Moon
          className={cn(
            'w-4 h-4 text-cyber-cyan transition-all duration-300 absolute',
            isDark
              ? 'opacity-100 rotate-0 scale-100'
              : 'opacity-0 -rotate-90 scale-50 pointer-events-none'
          )}
        />
      </div>

      {showLabel ? (
        <span className="font-mono text-[11px] font-semibold tracking-wider uppercase">
          {isDark ? 'Cyber Dark' : 'Light Mode'}
        </span>
      ) : (
        <span className="hidden md:inline font-mono text-[10px] uppercase tracking-wider text-slate-500 dark:text-navy-400 group-hover:text-slate-800 dark:group-hover:text-navy-200">
          {isDark ? 'Dark' : 'Light'}
        </span>
      )}

      {/* Subtle indicator dot */}
      <span
        className={cn(
          'w-1.5 h-1.5 rounded-full transition-colors',
          isDark ? 'bg-cyber-cyan shadow-cyan-glow' : 'bg-amber-500 shadow-warning-glow'
        )}
      />
    </button>
  );
};
