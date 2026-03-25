import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { describe, it, expect, afterEach, vi } from "vitest";
import { RequestHistory } from "../components/RequestHistory";

afterEach(cleanup);

vi.mock("../api/client", () => ({
  getGenerateStatus: vi
    .fn()
    .mockImplementation((id: string) =>
      Promise.resolve({
        id,
        channel_slug: "lofi",
        status: id === "req-1" ? "pending" : "completed",
        mood: id === "req-1" ? "calm" : null,
        caption: id === "req-2" ? "夕暮れのメロディ" : null,
        lyrics: null,
        bpm: null,
        duration: null,
        music_key: null,
        position: id === "req-1" ? 2 : null,
        created_at: "2026-03-25T00:00:00Z",
        started_at: null,
        completed_at: null,
        error_message: null,
        track: null,
      }),
    ),
}));

describe("RequestHistory", () => {
  it("renders nothing when requestIds is empty", () => {
    const { container } = render(<RequestHistory requestIds={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders header when requestIds provided", async () => {
    render(<RequestHistory requestIds={["req-1"]} />);
    await waitFor(() => {
      expect(screen.getByText("リクエスト履歴")).toBeInTheDocument();
    });
  });

  it("shows pending status for pending request", async () => {
    render(<RequestHistory requestIds={["req-1"]} />);
    await waitFor(() => {
      expect(screen.getByText("待機中")).toBeInTheDocument();
    });
  });

  it("shows completed status for completed request", async () => {
    render(<RequestHistory requestIds={["req-2"]} />);
    await waitFor(() => {
      expect(screen.getByText("完了")).toBeInTheDocument();
    });
  });

  it("shows queue position for pending request", async () => {
    render(<RequestHistory requestIds={["req-1"]} />);
    await waitFor(() => {
      expect(screen.getByText("#2")).toBeInTheDocument();
    });
  });

  it("shows caption or mood as label", async () => {
    render(<RequestHistory requestIds={["req-1", "req-2"]} />);
    await waitFor(() => {
      expect(screen.getByText("calm")).toBeInTheDocument();
      expect(screen.getByText("夕暮れのメロディ")).toBeInTheDocument();
    });
  });
});
