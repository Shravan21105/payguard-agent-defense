import React from 'react';
import { cn } from '../../utils/cn';

interface BadgeProps {
  type: 'ALLOW' | 'WARN' | 'BLOCK' | 'LOW' | 'MEDIUM' | 'HIGH' | 'PASSED' | 'FAILED' | 'BLOCKED' | 'WARNING' | 'PENDING' | 'APPROVED' | 'CONFIRMED' | 'ESCROW_CREATED' | string;
  className?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ type, className, size = 'md' }) => {
  const normalized = (type || '').toUpperCase();

  let colorClasses = 'bg-navy-800 text-navy-300 border-navy-700';
  let dotClasses = 'bg-navy-400';

  if (['ALLOW', 'LOW', 'PASSED', 'APPROVED', 'CONFIRMED', 'ONLINE', 'HEALTHY'].includes(normalized)) {
    colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-success-glow';
    dotClasses = 'bg-emerald-400';
  } else if (['WARN', 'MEDIUM', 'WARNING', 'PENDING', 'ESCROW_CREATED', 'DEGRADED'].includes(normalized)) {
    colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/30 shadow-warning-glow';
    dotClasses = 'bg-amber-400';
  } else if (['BLOCK', 'HIGH', 'FAILED', 'BLOCKED', 'CRITICAL', 'REJECTED', 'OFFLINE'].includes(normalized)) {
    colorClasses = 'bg-rose-500/10 text-rose-400 border-rose-500/30 shadow-danger-glow';
    dotClasses = 'bg-rose-400';
  } else if (['INFO', 'ANALYZING', 'RECEIVED', 'EXECUTING'].includes(normalized)) {
    colorClasses = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30 shadow-cyan-glow';
    dotClasses = 'bg-cyan-400';
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border tracking-wider font-mono font-medium uppercase backdrop-blur-sm select-none',
        sizeClasses,
        colorClasses,
        className
      )}
    >
      <span className="relative flex h-1.5 w-1.5">
        <span
          className={cn(
            'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
            dotClasses
          )}
        />
        <span className={cn('relative inline-flex rounded-full h-1.5 w-1.5', dotClasses)} />
      </span>
      {type}
    </span>
  );
};
