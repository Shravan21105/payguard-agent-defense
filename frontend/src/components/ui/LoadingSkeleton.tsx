import React from 'react';
import { cn } from '../../utils/cn';

interface LoadingSkeletonProps {
  className?: string;
  variant?: 'text' | 'card' | 'row' | 'circular';
  count?: number;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  className,
  variant = 'text',
  count = 1,
}) => {
  const items = Array.from({ length: count });

  const getVariantStyles = () => {
    switch (variant) {
      case 'card':
        return 'h-32 w-full rounded-xl';
      case 'row':
        return 'h-12 w-full rounded-lg';
      case 'circular':
        return 'h-10 w-10 rounded-full';
      case 'text':
      default:
        return 'h-4 w-3/4 rounded';
    }
  };

  return (
    <div className="space-y-3 w-full">
      {items.map((_, i) => (
        <div
          key={i}
          className={cn(
            'relative overflow-hidden bg-slate-200/80 dark:bg-navy-800/80 border border-slate-300/40 dark:border-white/[0.04]',
            getVariantStyles(),
            className
          )}
        >
          <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-slate-300/40 dark:via-white/[0.05] to-transparent animate-shimmer" />
        </div>
      ))}
    </div>
  );
};
