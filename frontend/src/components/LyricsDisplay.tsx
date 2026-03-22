import { useMemo, useRef, useEffect } from "react";

interface LyricsSection {
  header: string | null;
  lines: string[];
}

interface Props {
  lyrics: string;
  elapsedMs: number;
  durationMs: number;
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

export function LyricsDisplay({ lyrics, elapsedMs, durationMs }: Props) {
  const sections = useMemo(() => parseLyrics(lyrics), [lyrics]);
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const totalLines = sections.reduce(
    (sum, s) => sum + (s.header ? 1 : 0) + s.lines.length,
    0,
  );

  const progress = durationMs > 0 ? Math.min(elapsedMs / durationMs, 1) : 0;

  // Estimate which line index we're on
  const currentLineIndex = Math.floor(progress * totalLines);

  // Smooth scroll to estimated position
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
      className="glass-card p-5 max-h-72 overflow-hidden lyrics-mask"
    >
      <div className="text-xs uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>歌詞</div>
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
              className={`transition-all duration-700 ${
                isActiveSection
                  ? "opacity-100 scale-100"
                  : "opacity-40 scale-[0.98]"
              }`}
            >
              {section.header && (
                <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1.5">
                  {section.header}
                </div>
              )}
              {section.lines.map((line, li) => (
                <p key={li} className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
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
