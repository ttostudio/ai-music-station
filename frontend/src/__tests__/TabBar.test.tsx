import { describe, it, expect, vi, afterEach } from "vitest";
import { render, fireEvent, cleanup, within } from "@testing-library/react";
import { TabBar } from "../components/TabBar";

afterEach(cleanup);

describe("TabBar", () => {
  it("UT-TB-01: RADIO/TRACKS/LIKES/PLAYLISTS の4タブが描画される", () => {
    const { getByText } = render(<TabBar activeTab="radio" onChange={vi.fn()} />);
    expect(getByText("RADIO")).toBeInTheDocument();
    expect(getByText("TRACKS")).toBeInTheDocument();
    expect(getByText("LIKES")).toBeInTheDocument();
    expect(getByText("PLAYLISTS")).toBeInTheDocument();
  });

  it("UT-TB-02: 初期アクティブタブは RADIO", () => {
    const { getByRole } = render(<TabBar activeTab="radio" onChange={vi.fn()} />);
    const tablist = getByRole("tablist");
    const radioTab = within(tablist).getAllByRole("tab")[0];
    expect(radioTab).toHaveAttribute("aria-selected", "true");
  });

  it("UT-TB-03: TRACKS タブクリックで onChange('tracks') が呼ばれる", () => {
    const onChange = vi.fn();
    const { getByRole } = render(<TabBar activeTab="radio" onChange={onChange} />);
    const tablist = getByRole("tablist");
    const tracksTab = within(tablist).getAllByRole("tab")[1];
    fireEvent.click(tracksTab);
    expect(onChange).toHaveBeenCalledWith("tracks");
  });

  it("UT-TB-04: アクティブタブに tabbar-item-active クラスが付与される", () => {
    const { getByRole } = render(<TabBar activeTab="radio" onChange={vi.fn()} />);
    const tablist = getByRole("tablist");
    const radioTab = within(tablist).getAllByRole("tab")[0];
    expect(radioTab.className).toContain("tabbar-item-active");
  });

  it("UT-TB-06: 各タブに role='tab' が付与される（4タブ）", () => {
    const { getByRole } = render(<TabBar activeTab="radio" onChange={vi.fn()} />);
    const tablist = getByRole("tablist");
    const tabs = within(tablist).getAllByRole("tab");
    expect(tabs).toHaveLength(4);
  });

  it("UT-TB-07: タブリストに role='tablist' が付与される", () => {
    const { getAllByRole } = render(<TabBar activeTab="radio" onChange={vi.fn()} />);
    const tablists = getAllByRole("tablist");
    expect(tablists.length).toBeGreaterThanOrEqual(1);
  });

  it("TRACKS タブがアクティブな場合 TRACKS タブに aria-selected=true", () => {
    const { getByRole } = render(<TabBar activeTab="tracks" onChange={vi.fn()} />);
    const tablist = getByRole("tablist");
    const tabs = within(tablist).getAllByRole("tab");
    // TRACKS is index 1
    expect(tabs[1]).toHaveAttribute("aria-selected", "true");
    expect(tabs[0]).toHaveAttribute("aria-selected", "false");
  });
});
