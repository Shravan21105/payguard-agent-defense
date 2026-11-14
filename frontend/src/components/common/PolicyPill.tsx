import React from 'react';
import { cn } from '../../utils/cn';

interface PolicyPillProps {
  name: string;
  status: string;
}

export const PolicyPill: React.FC<PolicyPillProps> = ({ name, status }) => {
  const norm = (status || '').toUpperCase();

  const isPassed = norm === 'PASSED';
  const isWarn = norm === 'WARNING';
  const isBlocked = norm === 'BLOCKED' || norm === 'FAILED';

  const label = name.replace(/_/g, ' ');

  return (
    <div
      className={cn(
        'flex items-center justify-between px-3 py-2 rounded-lg border text-xs font-mono transition-all',
        {
          'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-300': isPassed,
          'bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-300': isWarn,
          'bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-300': isBlocked,
          'bg-slate-100 border-slate-200 text-slate-600 dark:bg-navy-800/60 dark:border-white/[0.08] dark:text-navy-400': !isPassed && !isWarn && !isBlocked,
        }
      )}
    >
      <span className="capitalize">{label}</span>
      <span
        className={cn('font-bold tracking-wider px-2 py-0.5 rounded text-[10px]', {
          'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400': isPassed,
          'bg-amber-500/20 text-amber-600 dark:text-amber-400': isWarn,
          'bg-rose-500/20 text-rose-600 dark:text-rose-400': isBlocked,
          'bg-slate-200 text-slate-700 dark:bg-navy-700 dark:text-navy-300': !isPassed && !isWarn && !isBlocked,
        })}
      >
        {status}
      </span>
    </div>
  );
};
