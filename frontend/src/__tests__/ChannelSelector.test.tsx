import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { ChannelSelector } from "../components/ChannelSelector";
import type { Channel } from "../api/types";

afterEach(cleanup);

const mockChannels: Channel[] = [
  {
    id: "1",
    slug: "lofi",
    name: "LoFi ビーツ",
    description: "チルなローファイ",
    is_active: true,
    queue_depth: 2,
    total_tracks: 10,
    stream_url: "/stream/lofi.ogg",
    now_playing: null,
  },
  {
    id: "2",
    slug: "jazz",
    name: "ジャズステーション",
    description: "スムースジャズ",
    is_active: true,
    queue_depth: 0,
    total_tracks: 5,
    stream_url: "/stream/jazz.ogg",
    now_playing: null,
  },
];

describe("ChannelSelector", () => {
  it("renders all channels", () => {
    render(
      <ChannelSelector
        channels={mockChannels}
        activeSlug={null}
        onSelect={() => {}}
      />,
    );
    expect(screen.getAllByText("LoFi ビーツ").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("ジャズステーション").length,
    ).toBeGreaterThan(0);
  });

  it("calls onSelect when channel is clicked", () => {
    const onSelect = vi.fn();
    render(
      <ChannelSelector
        channels={mockChannels}
        activeSlug={null}
        onSelect={onSelect}
      />,
    );
    fireEvent.click(screen.getAllByText("LoFi ビーツ")[0]);
    expect(onSelect).toHaveBeenCalledWith("lofi");
  });

  it("shows queue depth when non-zero", () => {
    render(
      <ChannelSelector
        channels={mockChannels}
        activeSlug={null}
        onSelect={() => {}}
      />,
    );
    expect(screen.getAllByText("(2件待ち)").length).toBeGreaterThan(0);
  });
});
