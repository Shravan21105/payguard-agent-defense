import React from 'react';
import { cn } from '../../utils/cn';

interface LiveIndicatorProps {
  status?: 'live' | 'syncing' | 'offline';
  label?: string;
  className?: string;
}

export const LiveIndicator: React.FC<LiveIndicatorProps> = ({
  status = 'live',
  label = 'LIVE',
  className,
}) => {
  const statusStyles = {
    live: {
      dot: 'bg-emerald-500 dark:bg-emerald-400',
      ping: 'bg-emerald-500 dark:bg-emerald-400',
      text: 'text-emerald-600 dark:text-emerald-400',
      badge: 'bg-emerald-500/10 border-emerald-500/30',
    },
    syncing: {
      dot: 'bg-amber-500 dark:bg-amber-400',
      ping: 'bg-amber-500 dark:bg-amber-400',
      text: 'text-amber-600 dark:text-amber-400',
      badge: 'bg-amber-500/10 border-amber-500/30',
    },
    offline: {
      dot: 'bg-rose-500 dark:bg-rose-400',
      ping: 'hidden',
      text: 'text-rose-600 dark:text-rose-400',
      badge: 'bg-rose-500/10 border-rose-500/30',
    },
  };

  const current = statusStyles[status];

  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 px-2.5 py-1 rounded-full border text-xs font-mono font-medium backdrop-blur-md',
        current.badge,
        current.text,
        className
      )}
    >
      <span className="relative flex h-2 w-2">
        <span
          className={cn(
            'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
            current.ping
          )}
        />
        <span className={cn('relative inline-flex rounded-full h-2 w-2', current.dot)} />
      </span>
      <span>{label}</span>
    </span>
  );
};

