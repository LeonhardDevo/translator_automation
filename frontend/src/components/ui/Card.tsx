import React from 'react';

type CardProps = React.HTMLAttributes<HTMLDivElement>;
export const Card: React.FC<CardProps> = ({ className, children, ...props }) => (
  <div 
    className={`rounded-xl border bg-white text-card-foreground shadow ${className}`} 
    {...props}
  >
    {children}
  </div>
);

type CardHeaderProps = React.HTMLAttributes<HTMLDivElement>;
export const CardHeader: React.FC<CardHeaderProps> = ({ className, children, ...props }) => (
  <div className={`flex flex-col space-y-1.5 p-6 ${className}`} {...props}>
    {children}
  </div>
);

type CardTitleProps = React.HTMLAttributes<HTMLHeadingElement>;
export const CardTitle: React.FC<CardTitleProps> = ({ className, children, ...props }) => (
  <h3 className={`font-semibold leading-none tracking-tight ${className}`} {...props}>
    {children}
  </h3>
);

type CardDescriptionProps = React.HTMLAttributes<HTMLParagraphElement>;
export const CardDescription: React.FC<CardDescriptionProps> = ({ className, children, ...props }) => (
  <p className={`text-sm text-muted-foreground ${className}`} {...props}>
    {children}
  </p>
);

type CardContentProps = React.HTMLAttributes<HTMLDivElement>;
export const CardContent: React.FC<CardContentProps> = ({ className, children, ...props }) => (
  <div className={`p-6 pt-0 ${className}`} {...props}>
    {children}
  </div>
);

type CardFooterProps = React.HTMLAttributes<HTMLDivElement>;
export const CardFooter: React.FC<CardFooterProps> = ({ className, children, ...props }) => (
  <div className={`flex items-center p-6 pt-0 ${className}`} {...props}>
    {children}
  </div>
);