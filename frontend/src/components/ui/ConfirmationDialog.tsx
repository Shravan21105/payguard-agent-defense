import React, { useEffect } from 'react';
import { AlertTriangle, ShieldCheck, X } from 'lucide-react';
import { cn } from '../../utils/cn';
import { GradientButton } from './GradientButton';

interface ConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  type?: 'danger' | 'warning' | 'success';
  isLoading?: boolean;
}

export const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = 'Confirm Action',
  cancelLabel = 'Cancel',
  type = 'warning',
  isLoading = false,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose, isLoading]);

  if (!isOpen) return null;

  const iconTypes = {
    danger: <AlertTriangle className="w-6 h-6 text-rose-500 dark:text-rose-400" />,
    warning: <AlertTriangle className="w-6 h-6 text-amber-500 dark:text-amber-400" />,
    success: <ShieldCheck className="w-6 h-6 text-emerald-500 dark:text-emerald-400" />,
  };

  const borderGlow = {
    danger: 'border-rose-500/40 shadow-danger-glow',
    warning: 'border-amber-500/40 shadow-warning-glow',
    success: 'border-emerald-500/40 shadow-success-glow',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-navy-950/80 backdrop-blur-md animate-fade-in-up">
      <div
        className={cn(
          'relative w-full max-w-md rounded-2xl bg-white/95 dark:bg-navy-800/95 border border-slate-200 dark:border-white/10 p-6 shadow-2xl backdrop-blur-xl',
          borderGlow[type]
        )}
      >
        <button
          onClick={onClose}
          disabled={isLoading}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-800 dark:text-navy-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-navy-700/50 transition"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-slate-100 dark:bg-navy-750 border border-slate-200 dark:border-white/10">
            {iconTypes[type]}
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white font-sans">{title}</h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-navy-300 font-sans leading-relaxed">{description}</p>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-white/[0.08]">
          <GradientButton
            variant="ghost"
            onClick={onClose}
            disabled={isLoading}
          >
            {cancelLabel}
          </GradientButton>
          <GradientButton
            variant={type === 'danger' ? 'danger' : type === 'success' ? 'success' : 'primary'}
            onClick={onConfirm}
            isLoading={isLoading}
          >
            {confirmLabel}
          </GradientButton>
        </div>
      </div>
    </div>
  );
};
