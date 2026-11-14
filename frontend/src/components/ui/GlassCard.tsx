import React from 'react';
import { cn } from '../../utils/cn';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'subtle' | 'interactive';
  glow?: 'none' | 'primary' | 'cyan' | 'emerald' | 'amber' | 'rose';
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className,
  variant = 'default',
  glow = 'none',
  ...props
}) => {
  const variantStyles = {
    default: 'bg-white/80 border-slate-200/90 shadow-sm dark:bg-navy-800/70 dark:border-white/[0.08] backdrop-blur-md',
    elevated: 'bg-white/95 border-slate-200/90 shadow-md dark:bg-navy-750/85 dark:border-white/[0.12] backdrop-blur-lg dark:shadow-glass-panel',
    subtle: 'bg-slate-50/80 border-slate-200/60 dark:bg-navy-900/60 dark:border-white/[0.05] backdrop-blur-sm',
    interactive: 'bg-white/80 border-slate-200/90 shadow-sm hover:border-cyber-indigo/40 hover:bg-white hover:shadow-md dark:bg-navy-800/70 dark:border-white/[0.08] dark:hover:border-cyber-indigo/40 dark:hover:bg-navy-800/90 dark:hover:shadow-primary-glow cursor-pointer transition-all duration-300',
  };

  const glowStyles = {
    none: '',
    primary: 'shadow-primary-glow border-cyber-indigo/30',
    cyan: 'shadow-cyan-glow border-cyber-cyan/30',
    emerald: 'shadow-success-glow border-emerald-500/30',
    amber: 'shadow-warning-glow border-amber-500/30',
    rose: 'shadow-danger-glow border-rose-500/30',
  };

  return (
    <div
      className={cn(
        'rounded-xl border transition-all duration-300',
        variantStyles[variant],
        glowStyles[glow],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
