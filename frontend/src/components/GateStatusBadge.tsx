import type { GateDecisionStatus } from "@/types";
import { Badge } from "@/components/ui/Badge";

interface StatusConfig {
  variant: "trust" | "warning" | "danger" | "muted";
  label: string;
  icon: string;
}

const STATUS_CONFIG: Record<GateDecisionStatus, StatusConfig> = {
  passed: { variant: "trust", label: "Passed", icon: "✓" },
  approved: { variant: "trust", label: "Approved", icon: "✓" },
  failed: { variant: "danger", label: "Failed", icon: "✗" },
  rejected: { variant: "danger", label: "Rejected", icon: "✗" },
  pending_approval: { variant: "warning", label: "Pending Approval", icon: "⏳" },
  overridden: { variant: "warning", label: "Overridden", icon: "⚡" },
};

interface Props {
  status: GateDecisionStatus;
}

export function GateStatusBadge({ status }: Props) {
  const { variant, label, icon } = STATUS_CONFIG[status] ?? {
    variant: "muted" as const,
    label: status,
    icon: "?",
  };
  return (
    <Badge variant={variant}>
      {icon} {label}
    </Badge>
  );
}
