import React from 'react';
import { cn } from '../../utils/cn';

interface RiskIndicatorProps {
  score: number;
  showLabel?: boolean;
  showTier?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const RiskIndicator: React.FC<RiskIndicatorProps> = ({
  score,
  showLabel = true,
  showTier = false,
  size = 'md',
  className,
}) => {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));

  let tier = 'LOW';
  let barGradient = 'from-emerald-500 to-teal-400';
  let textBadge = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
  let glowStyle = 'shadow-success-glow';

  if (clamped >= 70) {
    tier = 'HIGH';
    barGradient = 'from-rose-500 to-red-600';
    textBadge = 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    glowStyle = 'shadow-danger-glow';
  } else if (clamped >= 30) {
    tier = 'MEDIUM';
    barGradient = 'from-amber-500 to-orange-400';
    textBadge = 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    glowStyle = 'shadow-warning-glow';
  }

  const heightStyles = {
    sm: 'h-1.5 w-20',
    md: 'h-2 w-28',
    lg: 'h-3 w-40',
  };

  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div
        className={cn(
          'relative overflow-hidden rounded-full bg-slate-200 dark:bg-navy-900 border border-slate-300 dark:border-white/10',
          heightStyles[size]
        )}
      >
        <div
          className={cn(
            'h-full rounded-full bg-gradient-to-r transition-all duration-500',
            barGradient,
            glowStyle
          )}
          style={{ width: `${clamped}%` }}
        />
      </div>

      {showLabel && (
        <span className="font-mono font-bold text-xs text-slate-900 dark:text-white min-w-[32px]">
          {clamped}
          <span className="text-slate-500 dark:text-navy-400 font-normal">/100</span>
        </span>
      )}

      {showTier && (
        <span
          className={cn(
            'px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase border tracking-wider',
            textBadge
          )}
        >
          {tier}
        </span>
      )}
    </div>
  );
};

