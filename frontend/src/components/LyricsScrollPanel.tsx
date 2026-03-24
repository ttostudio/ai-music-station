import { useMemo, useRef, useEffect, useState, useCallback } from "react";
import {
  isLrcFormat, parseLrc, findLrcActiveIndex, computeCharProgress,
  getAllLines, computeActiveIndex, parseLyrics,
} from "../utils/lrc-parser";

interface Props {
  lyrics: string;
  elapsedMs: number;
  durationMs: number;
  variant?: "mobile" | "tablet" | "panel";
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

function useManualScrollPause(containerRef: React.RefObject<HTMLElement | null>) {
  const [paused, setPaused] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const programmaticScroll = useRef(false);

  const markProgrammatic = useCallback(() => {
    programmaticScroll.current = true;
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const handleScroll = () => {
      if (programmaticScroll.current) {
        programmaticScroll.current = false;
        return;
      }
      setPaused(true);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setPaused(false), 3000);
    };

    el.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      el.removeEventListener("scroll", handleScroll);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [containerRef]);

  return { paused, markProgrammatic };
}

export function LyricsScrollPanel({ lyrics, elapsedMs, durationMs, variant = "mobile" }: Props) {
  const lrcMode = useMemo(() => isLrcFormat(lyrics), [lyrics]);
  const lrcLines = useMemo(() => (lrcMode ? parseLrc(lyrics) : []), [lyrics, lrcMode]);
  const plainLines = useMemo(() => (lrcMode ? [] : getAllLines(lyrics)), [lyrics, lrcMode]);
  const sections = useMemo(() => (lrcMode ? [] : parseLyrics(lyrics)), [lyrics, lrcMode]);

  const activeLineRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const { paused, markProgrammatic } = useManualScrollPause(panelRef);

  const activeIndex = lrcMode
    ? findLrcActiveIndex(lrcLines, elapsedMs)
    : computeActiveIndex(elapsedMs, durationMs, plainLines.length);

  const charProgress = lrcMode
    ? computeCharProgress(lrcLines, activeIndex, elapsedMs, durationMs)
    : 0;

  useEffect(() => {
    if (paused) return;
    markProgrammatic();
    activeLineRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [activeIndex, paused, markProgrammatic]);

  const isTablet = variant === "tablet";
  const isPanel = variant === "panel";

  const getLineStyle = (diff: number): React.CSSProperties => {
    if (isTablet) {
      if (diff === 0) return { fontSize: 17, fontWeight: 700, color: "#FFD700" };
      if (diff === -1) return { color: "rgba(255,255,255,0.69)" };
      if (diff === 1) return { color: "rgba(255,255,255,0.38)" };
      if (diff < -1) return { color: "rgba(255,255,255,0.25)" };
      return { color: "rgba(255,255,255,0.25)" };
    }
    if (isPanel) {
      if (diff === 0) return { color: "#FFD700", fontWeight: 700 };
      if (diff < 0) return { color: "rgba(255,255,255,0.125)" };
      return { color: "rgba(255,255,255,0.25)" };
    }
    // mobile
    if (diff === 0) return { fontSize: 15, fontWeight: 700, color: "#FFD700" };
    if (diff === -1) return { fontSize: 14, color: "#4A4A60" };
    if (diff < -1) return { fontSize: 14, color: "#4A4A60" };
    if (diff === 1) return { fontSize: 14, color: "#C0C0D0" };
    return { fontSize: 14, color: "#6B6B80" };
  };

  if (lrcMode) {
    if (lrcLines.length === 0) return null;
    return (
      <div className={`lyrics-scroll-panel lyrics-scroll-${variant}`} ref={panelRef} role="log" aria-live="polite" aria-label="歌詞">
        <div className="lyrics-scroll-header">LYRICS</div>
        {lrcLines.map((lrcLine, i) => {
          const diff = i - activeIndex;
          const isActive = diff === 0;
          return (
            <div
              key={i}
              ref={isActive ? activeLineRef : undefined}
              className={`lyrics-scroll-line ${isActive ? "lyrics-scroll-line-active" : ""}`}
              style={getLineStyle(diff)}
            >
              {isActive && lrcMode ? (
                <KaraokeHighlightText text={lrcLine.text} progress={charProgress} />
              ) : (
                lrcLine.text
              )}
            </div>
          );
        })}
      </div>
    );
  }

  // Legacy (non-LRC)
  if (plainLines.length === 0) return null;

  let lineCounter = 0;
  const items: Array<
    | { type: "header"; content: string }
    | { type: "line"; content: string; lineIndex: number }
  > = [];

  for (const section of sections) {
    if (section.header) items.push({ type: "header", content: section.header });
    for (const line of section.lines) {
      items.push({ type: "line", content: line, lineIndex: lineCounter++ });
    }
  }

  return (
    <div className={`lyrics-scroll-panel lyrics-scroll-${variant}`} ref={panelRef} role="log" aria-live="polite" aria-label="歌詞">
      <div className="lyrics-scroll-header">LYRICS</div>
      {items.map((item, i) => {
        if (item.type === "header") {
          return (
            <div key={i} className="lyrics-scroll-section-header">{item.content}</div>
          );
        }
        const diff = item.lineIndex - activeIndex;
        const isActive = diff === 0;
        return (
          <div
            key={i}
            ref={isActive ? activeLineRef : undefined}
            className={`lyrics-scroll-line ${isActive ? "lyrics-scroll-line-active" : ""}`}
            style={getLineStyle(diff)}
          >
            {item.content}
          </div>
        );
      })}
    </div>
  );
}
