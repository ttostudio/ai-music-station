interface QualityScoreBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

type Grade = "A" | "B" | "C" | "D";

interface GradeInfo {
  grade: Grade;
  color: string;
  glow: string;
  label: string;
  icon: string;
}

function getGradeInfo(score: number): GradeInfo {
  if (score >= 80) {
    return {
      grade: "A",
      color: "#10B981",
      glow: "rgba(16, 185, 129, 0.2)",
      label: "非常に良好",
      icon: "✓",
    };
  }
  if (score >= 60) {
    return {
      grade: "B",
      color: "#3B82F6",
      glow: "rgba(59, 130, 246, 0.2)",
      label: "良好",
      icon: "",
    };
  }
  if (score >= 40) {
    return {
      grade: "C",
      color: "#F59E0B",
      glow: "rgba(245, 158, 11, 0.2)",
      label: "可",
      icon: "",
    };
  }
  return {
    grade: "D",
    color: "#EF4444",
    glow: "rgba(239, 68, 68, 0.2)",
    label: "低品質",
    icon: "⚠",
  };
}

const sizeStyles = {
  sm: { height: "24px", fontSize: "10px", padding: "0 6px" },
  md: { height: "28px", fontSize: "11px", padding: "0 8px" },
  lg: { height: "32px", fontSize: "11px", padding: "0 8px" },
};

export function QualityScoreBadge({
  score,
  size = "md",
  showLabel = true,
}: QualityScoreBadgeProps) {
  const info = getGradeInfo(score);
  const style = sizeStyles[size];

  return (
    <div
      className="badge-score inline-flex items-center gap-1 shrink-0"
      role="status"
      aria-label={`品質スコア ${Math.round(score)} 点、${info.label}`}
      style={{
        height: style.height,
        fontSize: style.fontSize,
        padding: style.padding,
        borderRadius: "9999px",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        background: `linear-gradient(135deg, var(--color-bg-card, #1A1A2E), ${info.glow})`,
        boxShadow: `0 2px 8px rgba(0, 0, 0, 0.3), 0 0 8px ${info.glow}`,
        color: info.color,
        fontWeight: 600,
        fontFamily: "var(--font-family)",
        transition: "transform 200ms ease, box-shadow 200ms ease",
        animation: "fade-in 300ms ease forwards",
      }}
    >
      <span className="badge-score-value tabular-nums">
        {info.icon && <span aria-hidden="true">{info.icon} </span>}
        {Math.round(score)}
      </span>
      {showLabel && (
        <span className="badge-score-label">{info.label}</span>
      )}
    </div>
  );
}
