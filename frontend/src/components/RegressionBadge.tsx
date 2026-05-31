import { Badge } from "@/components/ui/Badge";

interface RegressionBadgeProps {
  status: "regression" | "improvement" | "neutral";
  count?: number;
  className?: string;
}

const STATUS_CONFIG = {
  regression: { variant: "danger" as const, label: "Regression", icon: "▼" },
  improvement: { variant: "trust" as const, label: "Improvement", icon: "▲" },
  neutral: { variant: "muted" as const, label: "Neutral", icon: "—" },
};

export function RegressionBadge({ status, count, className }: RegressionBadgeProps) {
  const { variant, label, icon } = STATUS_CONFIG[status];
  const display = count !== undefined && count > 0 ? `${icon} ${label} (${count})` : `${icon} ${label}`;
  return (
    <Badge variant={variant} className={className}>
      {display}
    </Badge>
  );
}
