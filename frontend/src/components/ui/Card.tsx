import React from "react";

interface CardProps {
  className?: string;
  children: React.ReactNode;
}

export function Card({ className = "", children }: CardProps) {
  return (
    <div className={`rounded-lg border bg-card text-card-foreground shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ className = "", children }: CardProps) {
  return <div className={`p-4 pb-2 ${className}`}>{children}</div>;
}

export function CardBody({ className = "", children }: CardProps) {
  return <div className={`p-4 pt-0 ${className}`}>{children}</div>;
}
