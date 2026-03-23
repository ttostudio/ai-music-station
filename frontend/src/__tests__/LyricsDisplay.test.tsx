import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import { LyricsDisplay } from "../components/LyricsDisplay";

afterEach(cleanup);

const sampleLyrics = `[Verse]
夜空に輝く星たち
静かに流れる時間

[Chorus]
この瞬間を忘れない
永遠に続く melody`;

const simpleLyrics = "星空に浮かぶ\n君の笑顔が\n輝いている";

// ===== scroll-panel mode (Pattern A) =====

describe("LyricsDisplay scroll-panel mode", () => {
  it("renders lyrics lines", () => {
    render(
      <LyricsDisplay
        lyrics={sampleLyrics}
        elapsedMs={0}
        durationMs={180000}
        mode="scroll-panel"
      />,
    );
    expect(screen.getByText("夜空に輝く星たち")).toBeInTheDocument();
    expect(screen.getByText("この瞬間を忘れない")).toBeInTheDocument();
  });

  it("renders section headers", () => {
    render(
      <LyricsDisplay
        lyrics={sampleLyrics}
        elapsedMs={0}
        durationMs={180000}
        mode="scroll-panel"
      />,
    );
    expect(screen.getByText("Verse")).toBeInTheDocument();
    expect(screen.getByText("Chorus")).toBeInTheDocument();
  });

  it("renders LYRICS label", () => {
    render(
      <LyricsDisplay
        lyrics={sampleLyrics}
        elapsedMs={0}
        durationMs={180000}
        mode="scroll-panel"
      />,
    );
    expect(screen.getByText("LYRICS")).toBeInTheDocument();
  });

  it("returns null for empty lyrics", () => {
    const { container } = render(
      <LyricsDisplay
        lyrics=""
        elapsedMs={0}
        durationMs={180000}
        mode="scroll-panel"
      />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders the lyrics-panel container", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="scroll-panel"
      />,
    );
    expect(document.querySelector(".lyrics-panel")).toBeInTheDocument();
  });

  it("has aria-live polite for accessibility", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="scroll-panel"
      />,
    );
    const panel = document.querySelector(".lyrics-panel");
    expect(panel).toHaveAttribute("aria-live", "polite");
  });

  it("applies yellow color (#FFD700) to active line", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="scroll-panel"
      />,
    );
    // First line should be active at elapsedMs=0
    const firstLine = screen.getByText("星空に浮かぶ");
    expect(firstLine).toHaveStyle({ color: "#FFD700" });
  });

  it("renders lyrics without section headers", () => {
    render(
      <LyricsDisplay
        lyrics="ただの歌詞"
        elapsedMs={0}
        durationMs={180000}
        mode="scroll-panel"
      />,
    );
    expect(screen.getByText("ただの歌詞")).toBeInTheDocument();
  });
});

// ===== karaoke-overlay mode (Pattern B) =====

describe("LyricsDisplay karaoke-overlay mode", () => {
  it("renders karaoke-overlay class", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    expect(document.querySelector(".karaoke-overlay")).toBeInTheDocument();
  });

  it("renders all lyric lines", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    expect(screen.getByText("星空に浮かぶ")).toBeInTheDocument();
    expect(screen.getByText("君の笑顔が")).toBeInTheDocument();
    expect(screen.getByText("輝いている")).toBeInTheDocument();
  });

  it("has aria-live polite for accessibility", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    const overlay = document.querySelector(".karaoke-overlay");
    expect(overlay).toHaveAttribute("aria-live", "polite");
  });

  it("marks first line as active when elapsed is 0", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    const firstLine = screen.getByText("星空に浮かぶ");
    expect(firstLine.closest(".karaoke-line-active")).toBeInTheDocument();
  });

  it("applies yellow color (#FFD700) to active line", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    const firstLine = screen.getByText("星空に浮かぶ");
    expect(firstLine).toHaveStyle({ color: "#FFD700" });
  });

  it("excludes section headers from line rendering", () => {
    render(
      <LyricsDisplay
        lyrics={sampleLyrics}
        elapsedMs={0}
        durationMs={180000}
        mode="karaoke-overlay"
      />,
    );
    // Headers should not appear in karaoke mode
    expect(screen.queryByText("Verse")).not.toBeInTheDocument();
    expect(screen.queryByText("Chorus")).not.toBeInTheDocument();
    // Lines should appear
    expect(screen.getByText("夜空に輝く星たち")).toBeInTheDocument();
  });

  it("returns null for empty lyrics in karaoke mode", () => {
    const { container } = render(
      <LyricsDisplay
        lyrics=""
        elapsedMs={0}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    expect(container.innerHTML).toBe("");
  });
});

// ===== default mode (backward compat — falls back to karaoke-overlay) =====

describe("LyricsDisplay default mode", () => {
  it("defaults to karaoke-overlay when mode is omitted", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
      />,
    );
    expect(document.querySelector(".karaoke-overlay")).toBeInTheDocument();
  });
});

// ===== イントロオフセット補正テスト =====

describe("LyricsDisplay intro offset correction", () => {
  it("first line stays active during intro period (first 10% of duration)", () => {
    // durationMs=120000 → introOffset=12000ms
    // At elapsedMs=5000 (within intro), first line should still be active
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={5000}
        durationMs={120000}
        mode="scroll-panel"
      />,
    );
    const firstLine = screen.getByText("星空に浮かぶ");
    expect(firstLine).toHaveStyle({ color: "#FFD700" });
  });

  it("first line stays active at exactly intro boundary", () => {
    // durationMs=120000 → introOffset=12000ms
    // At elapsedMs=12000 (exact boundary), adjusted=0 → first line active
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={12000}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    const firstLine = screen.getByText("星空に浮かぶ");
    expect(firstLine).toHaveStyle({ color: "#FFD700" });
  });

  it("active line advances after intro offset in scroll-panel", () => {
    // durationMs=120000 → introOffset=12000, lyricsSpan=108000
    // 3 lines → each line spans 36000ms
    // At elapsedMs=50000 → adjusted=38000 → index=floor(38000/36000)=1 → 2nd line
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={50000}
        durationMs={120000}
        mode="scroll-panel"
      />,
    );
    const secondLine = screen.getByText("君の笑顔が");
    expect(secondLine).toHaveStyle({ color: "#FFD700" });
  });

  it("active line advances after intro offset in karaoke-overlay", () => {
    // Same calculation: elapsedMs=50000 → 2nd line active
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={50000}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    const secondLine = screen.getByText("君の笑顔が");
    expect(secondLine).toHaveStyle({ color: "#FFD700" });
    expect(secondLine.closest(".karaoke-line-active")).toBeInTheDocument();
  });

  it("last line is active near end of duration", () => {
    // At elapsedMs=119000 → adjusted=107000 → index=floor(107000/36000)=2 → 3rd line
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={119000}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    const thirdLine = screen.getByText("輝いている");
    expect(thirdLine).toHaveStyle({ color: "#FFD700" });
  });
});

// ===== 手動スクロール一時停止テスト =====

describe("LyricsDisplay manual scroll pause", () => {
  it("karaoke-overlay has scroll container for scroll detection", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    expect(document.querySelector(".karaoke-scroll-container")).toBeInTheDocument();
  });

  it("scroll-panel container supports scroll events", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="scroll-panel"
      />,
    );
    const panel = document.querySelector(".lyrics-panel");
    expect(panel).toBeInTheDocument();
    // Panel should be a scrollable container (role=log with aria-live)
    expect(panel).toHaveAttribute("role", "log");
  });
});

// ===== 非アクティブ行のスタイルテスト =====

describe("LyricsDisplay non-active line styles", () => {
  it("non-active lines have reduced opacity in karaoke mode", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    // 3rd line (future, not near) should have opacity < 1
    const thirdLine = screen.getByText("輝いている");
    const opacity = parseFloat(thirdLine.style.opacity);
    expect(opacity).toBeLessThan(1);
  });

  it("future-near line has higher opacity than distant future in karaoke mode", () => {
    // With 3 lines, at index 0: line 1 is futureNear (0.75), line 2 is future (0.5)
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="karaoke-overlay"
      />,
    );
    const nearLine = screen.getByText("君の笑顔が");
    const farLine = screen.getByText("輝いている");
    const nearOpacity = parseFloat(nearLine.style.opacity);
    const farOpacity = parseFloat(farLine.style.opacity);
    expect(nearOpacity).toBeGreaterThan(farOpacity);
  });

  it("past line has reduced opacity in scroll-panel mode", () => {
    // At elapsedMs=50000, index=1. Line 0 is past.
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={50000}
        durationMs={120000}
        mode="scroll-panel"
      />,
    );
    const pastLine = screen.getByText("星空に浮かぶ");
    const opacity = parseFloat(pastLine.style.opacity);
    expect(opacity).toBeLessThan(1);
  });
});

// ===== LRC形式パースとカラオケ表示テスト =====

const lrcLyrics = `[00:05.00]夜空に輝く星たち
[00:12.50]静かに流れる時間
[00:20.00]この瞬間を忘れない
[00:28.00]永遠に続く melody`;

describe("LyricsDisplay LRC format (karaoke-overlay)", () => {
  it("renders LRC lyrics with 2-line focus layout", () => {
    render(
      <LyricsDisplay
        lyrics={lrcLyrics}
        elapsedMs={6000}
        durationMs={60000}
        mode="karaoke-overlay"
      />,
    );
    // Active line (1st) should be visible
    expect(screen.getByText("夜空に輝く星たち")).toBeInTheDocument();
    // Next line should also be visible
    expect(screen.getByText("静かに流れる時間")).toBeInTheDocument();
    // LRC container should exist
    expect(document.querySelector(".karaoke-lrc-container")).toBeInTheDocument();
  });

  it("shows waiting state before first timestamp", () => {
    render(
      <LyricsDisplay
        lyrics={lrcLyrics}
        elapsedMs={2000}
        durationMs={60000}
        mode="karaoke-overlay"
      />,
    );
    // Before 5000ms, should show waiting state with first line
    expect(document.querySelector(".karaoke-lrc-waiting")).toBeInTheDocument();
    expect(screen.getByText("夜空に輝く星たち")).toBeInTheDocument();
  });

  it("advances to correct line based on timestamp", () => {
    render(
      <LyricsDisplay
        lyrics={lrcLyrics}
        elapsedMs={15000}
        durationMs={60000}
        mode="karaoke-overlay"
      />,
    );
    // At 15000ms, 2nd line (12500ms) should be active
    const activeLine = document.querySelector(".karaoke-lrc-active");
    expect(activeLine).toBeInTheDocument();
    expect(activeLine?.textContent).toBe("静かに流れる時間");
    // Next line should show
    const nextLine = document.querySelector(".karaoke-lrc-next");
    expect(nextLine?.textContent).toBe("この瞬間を忘れない");
  });

  it("uses character-level highlight on active line", () => {
    render(
      <LyricsDisplay
        lyrics={lrcLyrics}
        elapsedMs={8000}
        durationMs={60000}
        mode="karaoke-overlay"
      />,
    );
    // Active line should have karaoke-highlight-text span
    const highlight = document.querySelector(".karaoke-highlight-text");
    expect(highlight).toBeInTheDocument();
    // Should have background-clip: text for gradient effect
    expect(highlight).toHaveStyle({ backgroundClip: "text" });
  });

  it("last line has no next line displayed", () => {
    render(
      <LyricsDisplay
        lyrics={lrcLyrics}
        elapsedMs={30000}
        durationMs={60000}
        mode="karaoke-overlay"
      />,
    );
    // At 30000ms, 4th (last) line should be active
    const activeLine = document.querySelector(".karaoke-lrc-active");
    expect(activeLine?.textContent).toBe("永遠に続く melody");
    // No next line
    expect(document.querySelector(".karaoke-lrc-next")).toBeNull();
  });
});

describe("LyricsDisplay LRC format (scroll-panel)", () => {
  it("renders all LRC lines in scroll panel", () => {
    render(
      <LyricsDisplay
        lyrics={lrcLyrics}
        elapsedMs={6000}
        durationMs={60000}
        mode="scroll-panel"
      />,
    );
    expect(screen.getByText("夜空に輝く星たち")).toBeInTheDocument();
    expect(screen.getByText("静かに流れる時間")).toBeInTheDocument();
    expect(screen.getByText("この瞬間を忘れない")).toBeInTheDocument();
    expect(screen.getByText("永遠に続く melody")).toBeInTheDocument();
  });

  it("highlights active line with gradient in scroll panel", () => {
    render(
      <LyricsDisplay
        lyrics={lrcLyrics}
        elapsedMs={15000}
        durationMs={60000}
        mode="scroll-panel"
      />,
    );
    // 2nd line should have karaoke-highlight-text
    const highlight = document.querySelector(".karaoke-highlight-text");
    expect(highlight).toBeInTheDocument();
    expect(highlight?.textContent).toBe("静かに流れる時間");
  });

  it("non-LRC lyrics still work in scroll panel", () => {
    render(
      <LyricsDisplay
        lyrics={simpleLyrics}
        elapsedMs={0}
        durationMs={120000}
        mode="scroll-panel"
      />,
    );
    // Legacy mode: golden color, no gradient highlight
    expect(document.querySelector(".karaoke-highlight-text")).toBeNull();
    const firstLine = screen.getByText("星空に浮かぶ");
    expect(firstLine).toHaveStyle({ color: "#FFD700" });
  });
});
