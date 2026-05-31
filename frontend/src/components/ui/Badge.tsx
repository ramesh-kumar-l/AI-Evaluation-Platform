import React from "react";

interface BadgeProps {
  variant: "trust" | "warning" | "danger" | "muted";
  children: React.ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeProps["variant"], string> = {
  trust: "bg-trust/10 text-trust border-trust/30",
  warning: "bg-warning/10 text-warning border-warning/30",
  danger: "bg-danger/10 text-danger border-danger/30",
  muted: "bg-muted text-muted-foreground border-border",
};

export function Badge({ variant, children, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${variantClasses[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
