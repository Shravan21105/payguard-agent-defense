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
        'flex items-center justify-between px-2.5 py-1.5 rounded border text-xs font-mono',
        {
          'bg-emerald-950/30 border-emerald-800/40 text-emerald-300': isPassed,
          'bg-amber-950/30 border-amber-800/40 text-amber-300': isWarn,
          'bg-rose-950/30 border-rose-800/40 text-rose-300': isBlocked,
          'bg-charcoal-800/40 border-charcoal-700/40 text-charcoal-400': !isPassed && !isWarn && !isBlocked,
        }
      )}
    >
      <span className="capitalize">{label}</span>
      <span className="font-bold tracking-wide">{status}</span>
    </div>
  );
};
