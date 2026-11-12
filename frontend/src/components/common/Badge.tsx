import React from 'react';
import { cn } from '../../utils/cn';

interface BadgeProps {
  type: 'ALLOW' | 'WARN' | 'BLOCK' | 'LOW' | 'MEDIUM' | 'HIGH' | 'PASSED' | 'FAILED' | 'BLOCKED' | 'WARNING' | 'PENDING' | 'APPROVED' | string;
  className?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ type, className, size = 'md' }) => {
  const normalized = (type || '').toUpperCase();

  let colorClasses = 'bg-charcoal-800 text-charcoal-300 border-charcoal-700';

  if (['ALLOW', 'LOW', 'PASSED', 'APPROVED'].includes(normalized)) {
    colorClasses = 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60';
  } else if (['WARN', 'MEDIUM', 'WARNING', 'PENDING'].includes(normalized)) {
    colorClasses = 'bg-amber-950/60 text-amber-400 border-amber-800/60';
  } else if (['BLOCK', 'HIGH', 'FAILED', 'BLOCKED', 'CRITICAL'].includes(normalized)) {
    colorClasses = 'bg-rose-950/60 text-rose-400 border-rose-800/60';
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border tracking-wider font-mono font-medium uppercase',
        sizeClasses,
        colorClasses,
        className
      )}
    >
      <span
        className={cn('h-1.5 w-1.5 rounded-full', {
          'bg-emerald-400 animate-pulse': ['ALLOW', 'APPROVED'].includes(normalized),
          'bg-amber-400': ['WARN', 'PENDING', 'WARNING'].includes(normalized),
          'bg-rose-400': ['BLOCK', 'BLOCKED', 'FAILED', 'HIGH'].includes(normalized),
          'bg-charcoal-400': !['ALLOW', 'APPROVED', 'WARN', 'PENDING', 'WARNING', 'BLOCK', 'BLOCKED', 'FAILED', 'HIGH'].includes(normalized),
        })}
      />
      {type}
    </span>
  );
};
