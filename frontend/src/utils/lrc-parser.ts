export interface LrcLine {
  timeMs: number;
  text: string;
}

export interface LyricsSection {
  header: string | null;
  lines: string[];
}

const LRC_LINE_RE = /^\[(\d{1,3}):(\d{2})(?:\.(\d{1,3}))?\](.*)$/;

export function isLrcFormat(raw: string): boolean {
  const lines = raw.split("\n").slice(0, 10);
  return lines.some((l) => LRC_LINE_RE.test(l.trim()));
}

export function parseLrc(raw: string): LrcLine[] {
  const result: LrcLine[] = [];
  for (const line of raw.split("\n")) {
    const m = line.trim().match(LRC_LINE_RE);
    if (m) {
      const min = parseInt(m[1], 10);
      const sec = parseInt(m[2], 10);
      let ms = 0;
      if (m[3]) {
        const rawMs = m[3];
        ms = parseInt(rawMs.padEnd(3, "0").slice(0, 3), 10);
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

export function findLrcActiveIndex(lrcLines: LrcLine[], elapsedMs: number): number {
  if (lrcLines.length === 0) return -1;
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

export function computeCharProgress(
  lrcLines: LrcLine[],
  activeIndex: number,
  elapsedMs: number,
  durationMs: number,
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

export function parseLyrics(raw: string): LyricsSection[] {
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

export function getAllLines(lyrics: string): string[] {
  return lyrics
    .trim()
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .filter((l) => !l.match(/^\[.+\]$/));
}

export function computeActiveIndex(
  elapsedMs: number,
  durationMs: number,
  lineCount: number,
): number {
  if (durationMs <= 0 || lineCount <= 0) return 0;
  const introOffset = durationMs * 0.1;
  const adjusted = Math.max(0, elapsedMs - introOffset);
  const lyricsSpan = durationMs - introOffset;
  return Math.min(
    Math.floor(adjusted / (lyricsSpan / lineCount)),
    lineCount - 1,
  );
}

export function formatTime(ms: number): string {
  const totalSec = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function getChannelThemeKey(slug: string): string {
  if (slug.includes("anime")) return "anime";
  if (slug.includes("egushi") || slug.includes("えぐ")) return "egushi";
  if (slug.includes("game")) return "game";
  if (slug.includes("jazz")) return "jazz";
  if (slug.includes("podcast")) return "podcast";
  return "default";
}

export function getChannelGradient(slug: string): string {
  const key = getChannelThemeKey(slug);
  const map: Record<string, string> = {
    anime: "linear-gradient(135deg, #ec4899, #f472b6)",
    egushi: "linear-gradient(135deg, #8b5cf6, #a78bfa)",
    game: "linear-gradient(135deg, #059669, #34d399)",
    jazz: "linear-gradient(135deg, #d97706, #fbbf24)",
    podcast: "linear-gradient(135deg, #6366f1, #818cf8)",
    default: "linear-gradient(135deg, #6366f1, #818cf8)",
  };
  return map[key] || map.default;
}

export function getChannelColors(slug: string): [string, string] {
  const key = getChannelThemeKey(slug);
  const map: Record<string, [string, string]> = {
    anime: ["#ec4899", "#f472b6"],
    egushi: ["#8b5cf6", "#a78bfa"],
    game: ["#059669", "#34d399"],
    jazz: ["#d97706", "#fbbf24"],
    podcast: ["#6366f1", "#818cf8"],
    default: ["#6366f1", "#818cf8"],
  };
  return map[key] || map.default;
}
