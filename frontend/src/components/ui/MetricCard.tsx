import React from 'react';
import { cn } from '../../utils/cn';

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon: React.ReactNode;
  accentColor?: 'primary' | 'cyan' | 'emerald' | 'amber' | 'rose' | 'violet';
  trend?: {
    value: string;
    isPositive?: boolean;
    label?: string;
  };
  isLoading?: boolean;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subValue,
  icon,
  accentColor = 'primary',
  trend,
  isLoading = false,
  className,
}) => {
  const accentBorderStyles = {
    primary: 'border-l-4 border-l-cyber-indigo hover:border-cyber-indigo/50',
    cyan: 'border-l-4 border-l-cyber-cyan hover:border-cyber-cyan/50',
    emerald: 'border-l-4 border-l-emerald-500 hover:border-emerald-500/50',
    amber: 'border-l-4 border-l-amber-500 hover:border-amber-500/50',
    rose: 'border-l-4 border-l-rose-500 hover:border-rose-500/50',
    violet: 'border-l-4 border-l-violet-500 hover:border-violet-500/50',
  };

  const iconBgStyles = {
    primary: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20',
    cyan: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/20',
    emerald: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
    amber: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
    rose: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20',
    violet: 'bg-violet-500/10 text-violet-600 dark:text-violet-400 border-violet-500/20',
  };

  const valueColorStyles = {
    primary: 'text-slate-900 dark:text-white',
    cyan: 'text-cyan-600 dark:text-cyber-cyan',
    emerald: 'text-emerald-600 dark:text-emerald-400',
    amber: 'text-amber-600 dark:text-amber-400',
    rose: 'text-rose-600 dark:text-rose-400',
    violet: 'text-violet-600 dark:text-violet-400',
  };

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl bg-white/85 border border-slate-200/90 shadow-sm dark:bg-navy-800/80 dark:border-white/[0.08] backdrop-blur-md p-5 transition-all duration-300 hover:bg-white dark:hover:bg-navy-800/95 hover:shadow-md dark:hover:shadow-glass-panel',
        accentBorderStyles[accentColor],
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono font-medium tracking-wider uppercase text-slate-500 dark:text-navy-400">
          {label}
        </span>
        <div
          className={cn(
            'flex h-9 w-9 items-center justify-center rounded-lg border',
            iconBgStyles[accentColor]
          )}
        >
          {icon}
        </div>
      </div>

      <div className="mt-3">
        {isLoading ? (
          <div className="h-8 w-24 animate-pulse rounded bg-slate-200 dark:bg-navy-700" />
        ) : (
          <div className={cn('text-3xl font-bold font-mono tracking-tight', valueColorStyles[accentColor])}>
            {value}
          </div>
        )}

        <div className="mt-1 flex items-center justify-between text-[11px] font-mono text-slate-500 dark:text-navy-400">
          {subValue && <span>{subValue}</span>}
          {trend && (
            <span
              className={cn(
                'ml-auto font-medium',
                trend.isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
              )}
            >
              {trend.isPositive ? '+' : ''}
              {trend.value} {trend.label}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
