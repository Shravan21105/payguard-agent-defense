import React from 'react';
import { cn } from '../../utils/cn';

interface RiskMeterProps {
  score: number;
  className?: string;
  showLabel?: boolean;
}

export const RiskMeter: React.FC<RiskMeterProps> = ({ score, className, showLabel = true }) => {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));

  let barGradient = 'from-emerald-500 to-teal-400';
  let textColor = 'text-emerald-400';
  let glowStyle = 'shadow-success-glow';

  if (clamped >= 70) {
    barGradient = 'from-rose-500 to-red-600';
    textColor = 'text-rose-400';
    glowStyle = 'shadow-danger-glow';
  } else if (clamped >= 30) {
    barGradient = 'from-amber-500 to-orange-400';
    textColor = 'text-amber-400';
    glowStyle = 'shadow-warning-glow';
  }

  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div className="w-24 h-2 bg-navy-900 rounded-full overflow-hidden border border-white/10">
        <div
          className={cn('h-full rounded-full bg-gradient-to-r transition-all duration-500', barGradient, glowStyle)}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className={cn('text-xs font-mono font-bold min-w-[32px]', textColor)}>
          {clamped}/100
        </span>
      )}
    </div>
  );
};
