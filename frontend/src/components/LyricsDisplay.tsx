import { useMemo, useRef, useEffect } from "react";

interface LyricsSection {
  header: string | null;
  lines: string[];
}

interface Props {
  lyrics: string;
  elapsedMs: number;
  durationMs: number;
  mode?: "default" | "karaoke-overlay";
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

function getChannelGradient(slug: string | null | undefined): string {
  if (!slug) return "linear-gradient(135deg, #6366f1, #818cf8)";
  if (slug.includes("lofi") || slug.includes("lo-fi")) return "linear-gradient(135deg, #7c3aed, #a855f7)";
  if (slug.includes("anime")) return "linear-gradient(135deg, #ec4899, #f472b6)";
  if (slug.includes("jazz")) return "linear-gradient(135deg, #d97706, #fbbf24)";
  if (slug.includes("game")) return "linear-gradient(135deg, #059669, #34d399)";
  return "linear-gradient(135deg, #6366f1, #818cf8)";
}

export function LyricsDisplay({
  lyrics,
  elapsedMs,
  durationMs,
  mode = "default",
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
    <DefaultLyrics
      lyrics={lyrics}
      elapsedMs={elapsedMs}
      durationMs={durationMs}
    />
  );
}

// ===== Default mode (既存の動作) =====

function DefaultLyrics({
  lyrics,
  elapsedMs,
  durationMs,
}: {
  lyrics: string;
  elapsedMs: number;
  durationMs: number;
}) {
  const sections = useMemo(() => parseLyrics(lyrics), [lyrics]);
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const totalLines = sections.reduce(
    (sum, s) => sum + (s.header ? 1 : 0) + s.lines.length,
    0,
  );

  const progress = durationMs > 0 ? Math.min(elapsedMs / durationMs, 1) : 0;
  const currentLineIndex = Math.floor(progress * totalLines);

  useEffect(() => {
    const container = containerRef.current;
    const content = contentRef.current;
    if (!container || !content) return;

    const scrollableHeight = content.scrollHeight - container.clientHeight;
    if (scrollableHeight <= 0) return;

    const targetScroll = progress * scrollableHeight;
    container.scrollTo({ top: targetScroll, behavior: "smooth" });
  }, [progress]);

  if (sections.length === 0) return null;

  let lineCounter = 0;

  return (
    <div
      ref={containerRef}
      className="glass-card p-5 max-h-96 overflow-y-auto"
    >
      <div className="text-xs uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>歌詞</div>
      <div ref={contentRef} className="space-y-4">
        {sections.map((section, si) => {
          const sectionStartLine = lineCounter;
          const sectionLineCount =
            (section.header ? 1 : 0) + section.lines.length;
          lineCounter += sectionLineCount;
          const sectionEndLine = lineCounter;

          const isActiveSection =
            currentLineIndex >= sectionStartLine &&
            currentLineIndex < sectionEndLine;

          return (
            <div
              key={si}
              style={{
                transition: "opacity var(--transition-slow) var(--ease-smooth), transform var(--transition-slow) var(--ease-smooth)",
                opacity: isActiveSection ? 1 : 0.4,
                transform: isActiveSection ? "scale(1)" : "scale(0.98)",
              }}
            >
              {section.header && (
                <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1.5">
                  {section.header}
                </div>
              )}
              {section.lines.map((line, li) => (
                <p key={li} className="text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
                  {line}
                </p>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ===== Karaoke overlay mode =====

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

  const activeIndex =
    durationMs > 0 && lines.length > 0
      ? Math.min(
          Math.floor(elapsedMs / (durationMs / lines.length)),
          lines.length - 1
        )
      : 0;

  useEffect(() => {
    activeLineRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, [activeIndex]);

  if (lines.length === 0) return null;

  const gradient = getChannelGradient(channelSlug);

  return (
    <div
      className="karaoke-overlay"
      role="log"
      aria-live="polite"
      aria-label="歌詞"
    >
      <div className="karaoke-scroll-container">
        {lines.map((line, i) => {
          const isPast = i < activeIndex;
          const isActive = i === activeIndex;
          const isFuture = i > activeIndex;
          const isPastNear = i === activeIndex - 1;
          const isFutureNear = i === activeIndex + 1;

          let opacity = 1;
          let fontSize = "1rem";
          let color = "var(--text-primary)";

          if (isActive) {
            fontSize = "1.15rem";
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
          } else if (isFuture) {
            opacity = 0.5;
            fontSize = "0.9rem";
            color = "var(--text-secondary)";
          }

          return (
            <div
              key={i}
              ref={isActive ? activeLineRef : undefined}
              className={`karaoke-line ${isActive ? "karaoke-line-active" : ""}`}
              style={{
                opacity,
                fontSize,
                color: isActive ? "transparent" : color,
                fontWeight: isActive ? 700 : 400,
                background: isActive ? gradient : undefined,
                backgroundClip: isActive ? "text" : undefined,
                WebkitBackgroundClip: isActive ? "text" : undefined,
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
