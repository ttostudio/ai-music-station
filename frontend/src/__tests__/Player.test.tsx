import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import { Player } from "../components/Player";

afterEach(cleanup);

describe("Player", () => {
  it("renders channel name", () => {
    render(<Player streamUrl="/stream/lofi.ogg" channelName="LoFi Beats" />);
    expect(screen.getAllByText("LoFi Beats").length).toBeGreaterThan(0);
  });

  it("shows placeholder when no channel selected", () => {
    render(<Player streamUrl={null} channelName="" />);
    expect(screen.getAllByText("Select a channel").length).toBeGreaterThan(0);
  });

  it("has play button", () => {
    render(<Player streamUrl="/stream/lofi.ogg" channelName="LoFi" />);
    expect(screen.getAllByLabelText("Play").length).toBeGreaterThan(0);
  });

  it("has volume slider", () => {
    render(<Player streamUrl="/stream/lofi.ogg" channelName="LoFi" />);
    expect(screen.getAllByLabelText("Volume").length).toBeGreaterThan(0);
  });

  it("disables play button when no stream", () => {
    render(<Player streamUrl={null} channelName="" />);
    const btns = screen.getAllByLabelText("Play");
    expect(btns[0]).toBeDisabled();
  });
});
