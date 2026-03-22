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
