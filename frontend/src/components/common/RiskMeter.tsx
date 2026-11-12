import React from 'react';
import { cn } from '../../utils/cn';

interface RiskMeterProps {
  score: number;
  className?: string;
  showLabel?: boolean;
}

export const RiskMeter: React.FC<RiskMeterProps> = ({ score, className, showLabel = true }) => {
  const clamped = Math.max(0, Math.min(100, score));

  let barColor = 'bg-emerald-500';
  let textColor = 'text-emerald-400';

  if (clamped >= 70) {
    barColor = 'bg-rose-500';
    textColor = 'text-rose-400';
  } else if (clamped >= 30) {
    barColor = 'bg-amber-500';
    textColor = 'text-amber-400';
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="w-24 h-2 bg-charcoal-800 rounded-full overflow-hidden border border-charcoal-700/50">
        <div
          className={cn('h-full transition-all duration-500', barColor)}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className={cn('text-xs font-mono font-bold min-w-[28px]', textColor)}>
          {clamped}/100
        </span>
      )}
    </div>
  );
};
