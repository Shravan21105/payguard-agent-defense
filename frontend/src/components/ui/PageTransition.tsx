import React from 'react';
import { cn } from '../../utils/cn';

interface PageTransitionProps {
  children: React.ReactNode;
  className?: string;
}

export const PageTransition: React.FC<PageTransitionProps> = ({ children, className }) => {
  return (
    <div className={cn('animate-fade-in-up duration-300 w-full', className)}>
      {children}
    </div>
  );
};

