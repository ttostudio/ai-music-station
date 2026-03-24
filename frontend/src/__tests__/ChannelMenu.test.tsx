import { describe, it, expect, vi, afterEach } from "vitest";
import { render, fireEvent, cleanup } from "@testing-library/react";
import { ChannelMenu } from "../components/ChannelMenu";
import type { Channel } from "../api/types";

afterEach(cleanup);

const mockChannels: Channel[] = [
  {
    id: "1",
    slug: "anime",
    name: "Anime Songs",
    description: null,
    is_active: true,
    queue_depth: 2,
    total_tracks: 50,
    stream_url: "http://example.com/anime",
    now_playing: null,
  },
  {
    id: "2",
    slug: "jazz",
    name: "Jazz Vibes",
    description: null,
    is_active: true,
    queue_depth: 0,
    total_tracks: 30,
    stream_url: "http://example.com/jazz",
    now_playing: null,
  },
  {
    id: "3",
    slug: "game",
    name: "Game Music",
    description: null,
    is_active: false,
    queue_depth: 0,
    total_tracks: 20,
    stream_url: "http://example.com/game",
    now_playing: null,
  },
];

describe("ChannelMenu", () => {
  it("UT-CM-01: アクティブなチャンネルリストが全件表示される（非アクティブは除外）", () => {
    const { getByText, queryByText } = render(
      <ChannelMenu
        channels={mockChannels}
        activeSlug="anime"
        onSelect={vi.fn()}
        onManage={vi.fn()}
        onClose={vi.fn()}
      />
    );
    expect(getByText("Anime Songs")).toBeInTheDocument();
    expect(getByText("Jazz Vibes")).toBeInTheDocument();
    expect(queryByText("Game Music")).not.toBeInTheDocument();
  });

  it("UT-CM-02: アクティブチャンネルに強調スタイルが付与される", () => {
    const { container } = render(
      <ChannelMenu
        channels={mockChannels}
        activeSlug="anime"
        onSelect={vi.fn()}
        onManage={vi.fn()}
        onClose={vi.fn()}
      />
    );
    const menuItems = container.querySelectorAll(".channel-menu-item");
    const animeItem = Array.from(menuItems).find(el => el.textContent?.includes("Anime Songs")) as HTMLElement;
    expect(animeItem?.className).toMatch(/channel-active-/);
  });

  it("UT-CM-03: チャンネルクリックで onSelect(slug) が呼ばれる", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <ChannelMenu
        channels={mockChannels}
        activeSlug="anime"
        onSelect={onSelect}
        onManage={vi.fn()}
        onClose={vi.fn()}
      />
    );
    const menuItems = container.querySelectorAll(".channel-menu-item");
    const jazzItem = Array.from(menuItems).find(el => el.textContent?.includes("Jazz Vibes")) as HTMLElement;
    fireEvent.click(jazzItem);
    expect(onSelect).toHaveBeenCalledWith("jazz");
  });

  it("UT-CM-04: ⚙ ボタンクリックで onManage が呼ばれる", () => {
    const onManage = vi.fn();
    const { container } = render(
      <ChannelMenu
        channels={mockChannels}
        activeSlug="anime"
        onSelect={vi.fn()}
        onManage={onManage}
        onClose={vi.fn()}
      />
    );
    const manageBtn = container.querySelector(".channel-menu-manage-btn") as HTMLElement;
    fireEvent.click(manageBtn);
    expect(onManage).toHaveBeenCalled();
  });

  it("role='menu' が付与される", () => {
    const { container } = render(
      <ChannelMenu
        channels={mockChannels}
        activeSlug="anime"
        onSelect={vi.fn()}
        onManage={vi.fn()}
        onClose={vi.fn()}
      />
    );
    expect(container.querySelector("[role='menu']")).toBeInTheDocument();
  });

  it("Escape キーで onClose が呼ばれる", () => {
    const onClose = vi.fn();
    render(
      <ChannelMenu
        channels={mockChannels}
        activeSlug="anime"
        onSelect={vi.fn()}
        onManage={vi.fn()}
        onClose={onClose}
      />
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});
