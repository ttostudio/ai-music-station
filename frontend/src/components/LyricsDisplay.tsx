import { useMemo, useRef, useEffect, useState, useCallback } from "react";

// ===== Types =====

interface LyricsSection {
  header: string | null;
  lines: string[];
}

interface LrcLine {
  timeMs: number;
  text: string;
}

interface Props {
  lyrics: string;
  elapsedMs: number;
  durationMs: number;
  mode?: "karaoke-overlay" | "scroll-panel";
  channelSlug?: string | null;
}

// ===== LRC Parser =====

const LRC_LINE_RE = /^\[(\d{1,3}):(\d{2})(?:\.(\d{1,3}))?\](.*)$/;

/** LRC形式かどうか判定（最初の5行以内に[mm:ss.xx]パターンがあるか） */
function isLrcFormat(raw: string): boolean {
  const lines = raw.split("\n").slice(0, 10);
  return lines.some((l) => LRC_LINE_RE.test(l.trim()));
}

/** LRC形式をパース: [mm:ss.xx]テキスト → { timeMs, text }[] */
function parseLrc(raw: string): LrcLine[] {
  const result: LrcLine[] = [];
  for (const line of raw.split("\n")) {
    const m = line.trim().match(LRC_LINE_RE);
    if (m) {
      const min = parseInt(m[1], 10);
      const sec = parseInt(m[2], 10);
      // msパートは1〜3桁対応（.1=100ms, .12=120ms, .123=123ms）
      let ms = 0;
      if (m[3]) {
        const raw = m[3];
        ms = parseInt(raw.padEnd(3, "0").slice(0, 3), 10);
      }
      const timeMs = min * 60000 + sec * 1000 + ms;
      const text = m[4].trim();
      if (text) {
        result.push({ timeMs, text });
      }
    }
  }
  return result.sort((a, b) => a.timeMs - b.timeMs);
}

/** LRC行から現在のアクティブ行インデックスを取得 */
function findLrcActiveIndex(lrcLines: LrcLine[], elapsedMs: number): number {
  if (lrcLines.length === 0) return -1;
  // elapsedMs より前の最後の行を見つける
  let idx = -1;
  for (let i = 0; i < lrcLines.length; i++) {
    if (lrcLines[i].timeMs <= elapsedMs) {
      idx = i;
    } else {
      break;
    }
  }
  return idx;
}

/** アクティブ行内の文字進捗率 (0〜1) を計算 */
function computeCharProgress(
  lrcLines: LrcLine[],
  activeIndex: number,
  elapsedMs: number,
  durationMs: number
): number {
  if (activeIndex < 0 || activeIndex >= lrcLines.length) return 0;
  const startMs = lrcLines[activeIndex].timeMs;
  const endMs =
    activeIndex + 1 < lrcLines.length
      ? lrcLines[activeIndex + 1].timeMs
      : durationMs;
  const span = endMs - startMs;
  if (span <= 0) return 1;
  return Math.min(Math.max((elapsedMs - startMs) / span, 0), 1);
}

// ===== Legacy (non-LRC) helpers =====

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

// ===== Character-level highlight component =====

/** 文字レベルのカラオケハイライト表示 */
function KaraokeHighlightText({
  text,
  progress,
}: {
  text: string;
  progress: number;
}) {
  // CSS gradient で歌唱済み文字をシアン→ゴールドにハイライト
  const pct = Math.round(progress * 100);

  return (
    <span
      className="karaoke-highlight-text"
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

// ===== Main export =====

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
  const lrcMode = useMemo(() => isLrcFormat(lyrics), [lyrics]);
  const lrcLines = useMemo(() => (lrcMode ? parseLrc(lyrics) : []), [lyrics, lrcMode]);
  const plainLines = useMemo(() => (lrcMode ? [] : getAllLines(lyrics)), [lyrics, lrcMode]);

  const activeLineRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const { paused, markProgrammatic } = useManualScrollPause(scrollContainerRef);

  // LRCモード: タイムスタンプ基準、レガシーモード: 比率基準
  const activeIndex = lrcMode
    ? findLrcActiveIndex(lrcLines, elapsedMs)
    : computeActiveIndex(elapsedMs, durationMs, plainLines.length);

  const charProgress = lrcMode
    ? computeCharProgress(lrcLines, activeIndex, elapsedMs, durationMs)
    : 0;

  const lines = lrcMode ? lrcLines.map((l) => l.text) : plainLines;

  useEffect(() => {
    if (paused) return;
    markProgrammatic();
    activeLineRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, [activeIndex, paused, markProgrammatic]);

  if (lines.length === 0) return null;

  void channelSlug;

  // LRCモード: 2行フォーカス表示（現在行 + 次行）
  if (lrcMode) {
    return (
      <div
        className="karaoke-overlay"
        role="log"
        aria-live="polite"
        aria-label="歌詞"
      >
        <div className="karaoke-lrc-container">
          {/* 現在の行 */}
          {activeIndex >= 0 && (
            <div className="karaoke-lrc-active" ref={activeLineRef}>
              <KaraokeHighlightText
                text={lines[activeIndex]}
                progress={charProgress}
              />
            </div>
          )}

          {/* 次の行（歌い出し後のみ） */}
          {activeIndex >= 0 && activeIndex + 1 < lines.length && (
            <div className="karaoke-lrc-next">
              {lines[activeIndex + 1]}
            </div>
          )}

          {/* 歌い出し前 */}
          {activeIndex < 0 && (
            <div className="karaoke-lrc-waiting">
              {lines[0]}
            </div>
          )}
        </div>
      </div>
    );
  }

  // レガシーモード: 全行スクロール表示（既存動作）
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

// ===== Scroll panel mode =====

function ScrollPanel({
  lyrics,
  elapsedMs,
  durationMs,
}: {
  lyrics: string;
  elapsedMs: number;
  durationMs: number;
}) {
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
    activeLineRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, [activeIndex, paused, markProgrammatic]);

  // LRC scroll panel
  if (lrcMode) {
    if (lrcLines.length === 0) return null;

    return (
      <div className="lyrics-panel" ref={panelRef} role="log" aria-live="polite" aria-label="歌詞">
        <div
          className="text-xs uppercase tracking-widest mb-2 px-1"
          style={{ color: "var(--text-muted)" }}
        >
          LYRICS
        </div>
        {lrcLines.map((lrcLine, i) => {
          const diff = i - activeIndex;
          const isActive = diff === 0;

          let opacity = 1;
          let fontSize = "1rem";
          let fontWeight = 400;
          let color = "var(--text-primary)";

          if (isActive) {
            fontWeight = 700;
            fontSize = "1.05rem";
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
              ref={isActive ? activeLineRef : undefined}
              style={{
                opacity,
                fontSize,
                fontWeight,
                color: isActive ? undefined : color,
                lineHeight: 1.6,
                padding: "0.1rem 0.25rem",
                transition:
                  "opacity var(--transition-normal) var(--ease-smooth), color var(--transition-normal) var(--ease-smooth)",
              }}
            >
              {isActive ? (
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

  // Legacy scroll panel (non-LRC)
  if (plainLines.length === 0) return null;

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
