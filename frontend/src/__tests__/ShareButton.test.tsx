import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, fireEvent, cleanup, waitFor } from "@testing-library/react";
import { ShareButton } from "../components/ShareButton";
import * as client from "../api/client";

afterEach(cleanup);

describe("ShareButton", () => {
  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  it("UT-SB-01: trackId が null の場合ボタンが disabled になる", () => {
    const { container } = render(<ShareButton trackId={null} />);
    const btn = container.querySelector("[aria-label='シェア']") as HTMLButtonElement;
    expect(btn).toBeDisabled();
  });

  it("UT-SB-02: trackId が指定されている場合ボタンが enabled になる", () => {
    const { container } = render(<ShareButton trackId="track-1" />);
    const btn = container.querySelector("[aria-label='シェア']") as HTMLButtonElement;
    expect(btn).not.toBeDisabled();
  });

  it("UT-SB-03: クリック時に createShareLink が呼ばれる", async () => {
    const spy = vi.spyOn(client, "createShareLink").mockResolvedValue({
      share_url: "https://example.com/share/abc123",
      slug: "abc123",
      track_id: "track-1",
      created_at: "2026-03-24T00:00:00Z",
    });

    const { container } = render(<ShareButton trackId="track-1" />);
    const btn = container.querySelector("[aria-label='シェア']") as HTMLButtonElement;
    fireEvent.click(btn);

    await waitFor(() => expect(spy).toHaveBeenCalledWith("track-1"));
    spy.mockRestore();
  });

  it("UT-SB-04: コピー成功後にトースト「リンクをコピーしました」が表示される", async () => {
    vi.spyOn(client, "createShareLink").mockResolvedValue({
      share_url: "https://example.com/share/abc123",
      slug: "abc123",
      track_id: "track-1",
      created_at: "2026-03-24T00:00:00Z",
    });

    const { container } = render(<ShareButton trackId="track-1" />);
    const btn = container.querySelector("[aria-label='シェア']") as HTMLButtonElement;
    fireEvent.click(btn);

    await waitFor(() => {
      const toast = container.querySelector(".share-toast");
      expect(toast?.textContent).toBe("リンクをコピーしました");
    });
  });
});
