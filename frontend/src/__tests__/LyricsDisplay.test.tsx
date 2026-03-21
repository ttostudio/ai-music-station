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

describe("LyricsDisplay", () => {
  it("renders section headers", () => {
    render(
      <LyricsDisplay lyrics={sampleLyrics} elapsedMs={0} durationMs={180000} />,
    );
    expect(screen.getByText("Verse")).toBeInTheDocument();
    expect(screen.getByText("Chorus")).toBeInTheDocument();
  });

  it("renders lyrics lines", () => {
    render(
      <LyricsDisplay lyrics={sampleLyrics} elapsedMs={0} durationMs={180000} />,
    );
    expect(screen.getByText("夜空に輝く星たち")).toBeInTheDocument();
    expect(screen.getByText("この瞬間を忘れない")).toBeInTheDocument();
  });

  it("returns null for empty lyrics", () => {
    const { container } = render(
      <LyricsDisplay lyrics="" elapsedMs={0} durationMs={180000} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders lyrics without section headers", () => {
    render(
      <LyricsDisplay
        lyrics="ただの歌詞"
        elapsedMs={0}
        durationMs={180000}
      />,
    );
    expect(screen.getByText("ただの歌詞")).toBeInTheDocument();
  });

  it("shows lyrics label", () => {
    render(
      <LyricsDisplay lyrics={sampleLyrics} elapsedMs={0} durationMs={180000} />,
    );
    expect(screen.getByText("歌詞")).toBeInTheDocument();
  });
});
