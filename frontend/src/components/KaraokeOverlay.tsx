import { useMemo } from "react";
import { isLrcFormat, parseLrc, findLrcActiveIndex, computeCharProgress, getAllLines, computeActiveIndex } from "../utils/lrc-parser";

interface Props {
  lyrics: string;
  elapsedMs: number;
  durationMs: number;
  variant?: "mobile" | "desktop";
}

function KaraokeHighlightText({ text, progress }: { text: string; progress: number }) {
  const pct = Math.round(progress * 100);
  return (
    <span
      style={{
        background: `linear-gradient(to right, #00e5ff ${Math.max(0, pct - 2)}%, #FFD700 ${pct}%, rgba(255,255,255,0.5) ${pct + 1}%)`,
        WebkitBackgroundClip: "text",
        backgroundClip: "text",
        color: "transparent",
        WebkitTextFillColor: "transparent",
        textShadow: "none",
        filter: `drop-shadow(0 0 6px rgba(0, 229, 255, ${0.3 + progress * 0.4}))`,
      }}
    >
      {text}
    </span>
  );
}

export function KaraokeOverlay({ lyrics, elapsedMs, durationMs, variant = "desktop" }: Props) {
  const lrcMode = useMemo(() => isLrcFormat(lyrics), [lyrics]);
  const lrcLines = useMemo(() => (lrcMode ? parseLrc(lyrics) : []), [lyrics, lrcMode]);
  const plainLines = useMemo(() => (lrcMode ? [] : getAllLines(lyrics)), [lyrics, lrcMode]);

  const lines = lrcMode ? lrcLines.map((l) => l.text) : plainLines;
  const activeIndex = lrcMode
    ? findLrcActiveIndex(lrcLines, elapsedMs)
    : computeActiveIndex(elapsedMs, durationMs, plainLines.length);
  const charProgress = lrcMode
    ? computeCharProgress(lrcLines, activeIndex, elapsedMs, durationMs)
    : 0;

  if (lines.length === 0) return null;

  const prevLine = activeIndex > 0 ? lines[activeIndex - 1] : "";
  const currentLine = activeIndex >= 0 ? lines[activeIndex] : lines[0];
  const nextLine = activeIndex >= 0 && activeIndex + 1 < lines.length ? lines[activeIndex + 1] : "";
  const isDesktop = variant === "desktop";

  return (
    <div
      className={`karaoke-overlay-new ${isDesktop ? "karaoke-overlay-desktop" : "karaoke-overlay-mobile"}`}
      role="log"
      aria-live="polite"
      aria-atomic="true"
      aria-label="歌詞"
    >
      {prevLine && <div className="karaoke-prev-line">{prevLine}</div>}
      <div className="karaoke-current-line">
        {lrcMode && activeIndex >= 0 ? (
          <KaraokeHighlightText text={currentLine} progress={charProgress} />
        ) : (
          currentLine
        )}
      </div>
      {nextLine && <div className="karaoke-next-line-new">{nextLine}</div>}
      {activeIndex < 0 && (
        <div className="karaoke-waiting">{lines[0]}</div>
      )}
    </div>
  );
}
