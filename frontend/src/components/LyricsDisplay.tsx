import { useMemo, useRef, useEffect, useState, useCallback } from "react";

interface LyricsSection {
  header: string | null;
  lines: string[];
}

interface Props {
  lyrics: string;
  elapsedMs: number;
  durationMs: number;
  mode?: "karaoke-overlay" | "scroll-panel";
  channelSlug?: string | null;
}

function parseLyrics(raw: string): LyricsSection[] {
  const sections: LyricsSection[] = [];
  let current: LyricsSection = { header: null, lines: [] };

  for (const line of raw.split("\n")) {
    const headerMatch = line.match(/^\[(.+)\]$/);
    if (headerMatch) {
      if (current.header !== null || current.lines.length > 0) {
        sections.push(current);
      }
      current = { header: headerMatch[1], lines: [] };
    } else if (line.trim()) {
      current.lines.push(line.trim());
    }
  }

  if (current.header !== null || current.lines.length > 0) {
    sections.push(current);
  }

  return sections;
}

function getAllLines(lyrics: string): string[] {
  return lyrics
    .trim()
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .filter((l) => !l.match(/^\[.+\]$/));
}

/** イントロオフセット: 全体の10%をイントロ無音区間として補正 */
function computeActiveIndex(
  elapsedMs: number,
  durationMs: number,
  lineCount: number
): number {
  if (durationMs <= 0 || lineCount <= 0) return 0;
  const introOffset = durationMs * 0.1;
  const adjusted = Math.max(0, elapsedMs - introOffset);
  const lyricsSpan = durationMs - introOffset;
  return Math.min(
    Math.floor(adjusted / (lyricsSpan / lineCount)),
    lineCount - 1
  );
}

/** 手動スクロール検出フック: ユーザーがスクロールしたら3秒間自動スクロールを停止 */
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

export function LyricsDisplay({
  lyrics,
  elapsedMs,
  durationMs,
  mode = "karaoke-overlay",
  channelSlug,
}: Props) {
  if (mode === "karaoke-overlay") {
    return (
      <KaraokeOverlay
        lyrics={lyrics}
        elapsedMs={elapsedMs}
        durationMs={durationMs}
        channelSlug={channelSlug}
      />
    );
  }

  return (
    <ScrollPanel
      lyrics={lyrics}
      elapsedMs={elapsedMs}
      durationMs={durationMs}
    />
  );
}

// ===== Karaoke overlay mode (Pattern B) =====

function KaraokeOverlay({
  lyrics,
  elapsedMs,
  durationMs,
  channelSlug,
}: {
  lyrics: string;
  elapsedMs: number;
  durationMs: number;
  channelSlug?: string | null;
}) {
  const lines = useMemo(() => getAllLines(lyrics), [lyrics]);
  const activeLineRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const { paused, markProgrammatic } = useManualScrollPause(scrollContainerRef);

  const activeIndex = computeActiveIndex(elapsedMs, durationMs, lines.length);

  useEffect(() => {
    if (paused) return;
    markProgrammatic();
    activeLineRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, [activeIndex, paused, markProgrammatic]);

  if (lines.length === 0) return null;

  // channelSlug is retained for potential future use (e.g. themed glow color)
  void channelSlug;

  return (
    <div
      className="karaoke-overlay"
      role="log"
      aria-live="polite"
      aria-label="歌詞"
    >
      <div className="karaoke-scroll-container" ref={scrollContainerRef}>
        {lines.map((line, i) => {
          const isPast = i < activeIndex;
          const isActive = i === activeIndex;
          const isFuture = i > activeIndex;
          const isPastNear = i === activeIndex - 1;
          const isFutureNear = i === activeIndex + 1;

          let opacity = 1;
          let fontSize = "1rem";
          let color = "var(--text-primary)";
          let textShadow: string | undefined;
          let extraClass = "";

          if (isActive) {
            fontSize = "1.15rem";
            color = "#FFD700";
            textShadow = "0 0 8px rgba(255, 215, 0, 0.6), 0 2px 4px rgba(0, 0, 0, 0.8)";
          } else if (isPastNear) {
            opacity = 0.4;
            fontSize = "0.95rem";
            color = "var(--text-secondary)";
          } else if (isPast) {
            opacity = 0.25;
            fontSize = "0.85rem";
            color = "var(--text-muted)";
          } else if (isFutureNear) {
            opacity = 0.75;
            extraClass = "karaoke-next-line";
          } else if (isFuture) {
            opacity = 0.5;
            fontSize = "0.9rem";
            color = "var(--text-secondary)";
          }

          return (
            <div
              key={i}
              ref={isActive ? activeLineRef : undefined}
              className={`karaoke-line ${isActive ? "karaoke-line-active" : ""} ${extraClass}`.trim()}
              style={{
                opacity,
                fontSize,
                color,
                fontWeight: isActive ? 700 : 400,
                textShadow,
              }}
            >
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ===== Scroll panel mode (Pattern A) =====

function ScrollPanel({
  lyrics,
  elapsedMs,
  durationMs,
}: {
  lyrics: string;
  elapsedMs: number;
  durationMs: number;
}) {
  const lines = useMemo(() => getAllLines(lyrics), [lyrics]);
  const sections = useMemo(() => parseLyrics(lyrics), [lyrics]);
  const activeLineRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const { paused, markProgrammatic } = useManualScrollPause(panelRef);

  const activeIndex = computeActiveIndex(elapsedMs, durationMs, lines.length);

  useEffect(() => {
    if (paused) return;
    markProgrammatic();
    activeLineRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, [activeIndex, paused, markProgrammatic]);

  if (lines.length === 0) return null;

  // Build flat item list: headers + lines with flat line index
  let lineCounter = 0;
  const items: Array<
    | { type: "header"; content: string }
    | { type: "line"; content: string; lineIndex: number }
  > = [];

  for (const section of sections) {
    if (section.header) {
      items.push({ type: "header", content: section.header });
    }
    for (const line of section.lines) {
      items.push({ type: "line", content: line, lineIndex: lineCounter++ });
    }
  }

  return (
    <div className="lyrics-panel" ref={panelRef} role="log" aria-live="polite" aria-label="歌詞">
      <div
        className="text-xs uppercase tracking-widest mb-2 px-1"
        style={{ color: "var(--text-muted)" }}
      >
        LYRICS
      </div>
      {items.map((item, i) => {
        if (item.type === "header") {
          return (
            <div
              key={i}
              className="text-xs font-semibold uppercase tracking-wider mt-2 mb-1 px-1"
              style={{ color: "var(--text-muted)", opacity: 0.7 }}
            >
              {item.content}
            </div>
          );
        }

        const diff = item.lineIndex - activeIndex;
        let opacity = 1;
        let fontSize = "1rem";
        let fontWeight = 400;
        let color = "var(--text-primary)";
        let textShadow: string | undefined;

        if (diff === 0) {
          fontWeight = 700;
          color = "#FFD700";
          textShadow = "0 0 12px rgba(255,215,0,0.6)";
        } else if (diff === -1) {
          opacity = 0.45;
          fontSize = "0.90rem";
          color = "var(--text-secondary)";
        } else if (diff < -1) {
          opacity = 0.25;
          fontSize = "0.80rem";
          color = "var(--text-muted)";
        } else if (diff === 1) {
          opacity = 0.65;
          fontSize = "0.90rem";
        } else {
          opacity = 0.45;
          fontSize = "0.85rem";
          color = "var(--text-secondary)";
        }

        return (
          <div
            key={i}
            ref={diff === 0 ? activeLineRef : undefined}
            style={{
              opacity,
              fontSize,
              fontWeight,
              color,
              textShadow,
              lineHeight: 1.6,
              padding: "0.1rem 0.25rem",
              transition:
                "opacity var(--transition-normal) var(--ease-smooth), color var(--transition-normal) var(--ease-smooth)",
            }}
          >
            {item.content}
          </div>
        );
      })}
    </div>
  );
}
