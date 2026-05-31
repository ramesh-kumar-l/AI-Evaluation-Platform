import { Badge } from "@/components/ui/Badge";
import { confidenceVariant } from "@/lib/utils";

interface TrustIndicatorProps {
  confidence: string;
  label?: string;
}

const CONFIDENCE_LABELS: Record<string, string> = {
  high: "High confidence",
  medium: "Medium confidence",
  low: "Low confidence",
};

const CONFIDENCE_DOTS: Record<string, string> = {
  high: "●",
  medium: "◑",
  low: "○",
};

export function TrustIndicator({ confidence, label }: TrustIndicatorProps) {
  const variant = confidenceVariant(confidence);
  const displayLabel = label ?? CONFIDENCE_LABELS[confidence] ?? confidence;
  const dot = CONFIDENCE_DOTS[confidence] ?? "○";

  return (
    <Badge variant={variant} className="gap-1">
      <span aria-hidden="true">{dot}</span>
      {displayLabel}
    </Badge>
  );
}
