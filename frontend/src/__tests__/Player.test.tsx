import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import { Player } from "../components/Player";

afterEach(cleanup);

describe("Player", () => {
  it("renders channel name", () => {
    render(<Player streamUrl="/stream/lofi.ogg" channelName="LoFi ビーツ" />);
    expect(screen.getAllByText("LoFi ビーツ").length).toBeGreaterThan(0);
  });

  it("shows placeholder when no channel selected", () => {
    render(<Player streamUrl={null} channelName="" />);
    expect(
      screen.getAllByText("チャンネルを選択してください").length,
    ).toBeGreaterThan(0);
  });

  it("has play button", () => {
    render(<Player streamUrl="/stream/lofi.ogg" channelName="LoFi" />);
    expect(screen.getAllByLabelText("再生").length).toBeGreaterThan(0);
  });

  it("has volume slider", () => {
    render(<Player streamUrl="/stream/lofi.ogg" channelName="LoFi" />);
    expect(screen.getAllByLabelText("音量").length).toBeGreaterThan(0);
  });

  it("disables play button when no stream", () => {
    render(<Player streamUrl={null} channelName="" />);
    const btns = screen.getAllByLabelText("再生");
    expect(btns[0]).toBeDisabled();
  });
});
