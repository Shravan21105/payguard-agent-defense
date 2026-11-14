import React from 'react';
import { cn } from '../../utils/cn';

interface GradientButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'glass' | 'danger' | 'success' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const GradientButton: React.FC<GradientButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  disabled,
  ...props
}) => {
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5',
    md: 'px-4 py-2 text-sm rounded-lg gap-2',
    lg: 'px-6 py-3 text-base rounded-xl gap-2.5 font-semibold',
  };

  const variantStyles = {
    primary:
      'bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 text-white shadow-primary-glow hover:from-blue-500 hover:via-indigo-500 hover:to-violet-500 active:scale-[0.98] border border-white/20',
    secondary:
      'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-cyan-glow hover:from-cyan-400 hover:to-blue-500 active:scale-[0.98] border border-white/20',
    glass:
      'bg-white/80 dark:bg-navy-800/80 backdrop-blur-md text-slate-800 dark:text-navy-100 border border-slate-200/90 dark:border-white/10 hover:border-cyber-indigo/40 hover:bg-white dark:hover:bg-navy-750 shadow-sm dark:shadow-none active:scale-[0.98]',
    danger:
      'bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-danger-glow hover:from-red-500 hover:to-rose-500 active:scale-[0.98] border border-white/10',
    success:
      'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-success-glow hover:from-emerald-500 hover:to-teal-500 active:scale-[0.98] border border-white/10',
    ghost:
      'bg-transparent text-slate-600 dark:text-navy-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-navy-800/60 active:scale-[0.98]',
    outline:
      'bg-transparent border border-slate-300 dark:border-navy-600 text-slate-700 dark:text-navy-200 hover:text-slate-900 dark:hover:text-white hover:border-cyber-indigo/60 hover:bg-slate-100/60 dark:hover:bg-navy-800/30 active:scale-[0.98]',
  };

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center font-medium font-sans tracking-wide transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none select-none',
        sizeStyles[size],
        variantStyles[variant],
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4 text-current" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span>Processing...</span>
        </span>
      ) : (
        <>
          {leftIcon}
          {children}
          {rightIcon}
        </>
      )}
    </button>
  );
};
