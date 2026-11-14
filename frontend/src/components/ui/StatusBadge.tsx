import React from 'react';
import { cn } from '../../utils/cn';

interface StatusBadgeProps {
  status: 'ALLOW' | 'WARN' | 'BLOCK' | 'LOW' | 'MEDIUM' | 'HIGH' | 'PASSED' | 'FAILED' | 'BLOCKED' | 'WARNING' | 'PENDING' | 'APPROVED' | 'CONFIRMED' | 'ESCROW_CREATED' | 'INFO' | string;
  className?: string;
  size?: 'xs' | 'sm' | 'md';
  pulse?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  className,
  size = 'sm',
  pulse = true,
}) => {
  const norm = (status || '').toUpperCase();

  let colorStyles = 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-navy-800 dark:text-navy-300 dark:border-navy-700';
  let dotStyles = 'bg-slate-400 dark:bg-navy-400';

  if (['ALLOW', 'LOW', 'PASSED', 'APPROVED', 'CONFIRMED', 'ONLINE', 'HEALTHY'].includes(norm)) {
    colorStyles = 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30 shadow-success-glow';
    dotStyles = 'bg-emerald-500 dark:bg-emerald-400';
  } else if (['WARN', 'MEDIUM', 'WARNING', 'PENDING', 'ESCROW_CREATED', 'DEGRADED'].includes(norm)) {
    colorStyles = 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30 shadow-warning-glow';
    dotStyles = 'bg-amber-500 dark:bg-amber-400';
  } else if (['BLOCK', 'HIGH', 'FAILED', 'BLOCKED', 'CRITICAL', 'REJECTED', 'OFFLINE'].includes(norm)) {
    colorStyles = 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/30 shadow-danger-glow';
    dotStyles = 'bg-rose-500 dark:bg-rose-400';
  } else if (['INFO', 'ANALYZING', 'RECEIVED', 'EXECUTING'].includes(norm)) {
    colorStyles = 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 border-cyan-500/30 shadow-cyan-glow';
    dotStyles = 'bg-cyan-500 dark:bg-cyan-400';
  }

  const sizeStyles = {
    xs: 'px-2 py-0.5 text-[10px]',
    sm: 'px-2.5 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm font-semibold',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border font-mono font-medium uppercase tracking-wider backdrop-blur-sm select-none',
        sizeStyles[size],
        colorStyles,
        className
      )}
    >
      <span className="relative flex h-1.5 w-1.5">
        {pulse && (
          <span
            className={cn(
              'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
              dotStyles
            )}
          />
        )}
        <span className={cn('relative inline-flex rounded-full h-1.5 w-1.5', dotStyles)} />
      </span>
      <span>{status}</span>
    </span>
  );
};
