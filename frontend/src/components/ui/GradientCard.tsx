import React from 'react';
import { cn } from '../../utils/cn';

interface GradientCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  gradient?: 'primary' | 'cyan' | 'violet' | 'emerald' | 'danger';
}

export const GradientCard: React.FC<GradientCardProps> = ({
  children,
  className,
  gradient = 'primary',
  ...props
}) => {
  const gradientStyles = {
    primary: 'from-blue-600/20 via-indigo-600/10 to-transparent border-indigo-500/30 hover:border-indigo-500/60 shadow-primary-glow',
    cyan: 'from-cyan-500/20 via-blue-600/10 to-transparent border-cyan-500/30 hover:border-cyan-400/60 shadow-cyan-glow',
    violet: 'from-violet-600/20 via-purple-600/10 to-transparent border-violet-500/30 hover:border-violet-400/60',
    emerald: 'from-emerald-600/20 via-teal-600/10 to-transparent border-emerald-500/30 hover:border-emerald-400/60 shadow-success-glow',
    danger: 'from-rose-600/20 via-red-600/10 to-transparent border-rose-500/30 hover:border-rose-400/60 shadow-danger-glow',
  };

  return (
    <div
      className={cn(
        'relative rounded-xl border bg-gradient-to-br bg-white/90 dark:bg-navy-850/80 backdrop-blur-md shadow-sm dark:shadow-none transition-all duration-300',
        gradientStyles[gradient],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

