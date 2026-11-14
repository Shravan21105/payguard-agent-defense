import React from 'react';
import { cn } from '../../utils/cn';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-12 text-center rounded-xl bg-white/70 dark:bg-navy-800/40 border border-slate-200/80 dark:border-white/[0.06] backdrop-blur-sm shadow-sm dark:shadow-none',
        className
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 dark:bg-navy-750/80 border border-slate-200 dark:border-white/10 text-cyber-indigo mb-4 shadow-sm dark:shadow-glass-edge">
        {icon}
      </div>
      <h3 className="text-base font-semibold text-slate-900 dark:text-white font-sans">{title}</h3>
      <p className="mt-1 text-sm text-slate-600 dark:text-navy-400 max-w-md font-sans">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
};
