import { formatTime } from "../utils/lrc-parser";

interface Props {
  currentMs: number;
  totalMs: number;
}

export function ProgressBar({ currentMs, totalMs }: Props) {
  const pct = totalMs > 0 ? Math.min((currentMs / totalMs) * 100, 100) : 0;

  return (
    <div className="progress-bar-wrapper">
      <div className="progress-bar-track" role="slider" aria-valuenow={currentMs} aria-valuemin={0} aria-valuemax={totalMs} aria-label="再生位置">
        <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="progress-bar-times">
        <span>{formatTime(currentMs)}</span>
        <span>{formatTime(totalMs)}</span>
      </div>
    </div>
  );
}
