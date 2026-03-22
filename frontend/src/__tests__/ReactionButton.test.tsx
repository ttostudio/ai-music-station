import { render, screen, fireEvent, cleanup, waitFor } from "@testing-library/react";
import { describe, it, expect, afterEach, vi } from "vitest";
import { ReactionButton } from "../components/ReactionButton";
import { getReaction, addReaction, removeReaction } from "../api/client";

afterEach(cleanup);

// Mock the API client
vi.mock("../api/client", () => ({
  getReaction: vi.fn().mockResolvedValue({ count: 5, user_reacted: false }),
  addReaction: vi.fn().mockResolvedValue({ ok: true, count: 6 }),
  removeReaction: vi.fn().mockResolvedValue({ ok: true, count: 4 }),
}));

describe("ReactionButton", () => {
  it("renders the like button", () => {
    render(<ReactionButton trackId="track-1" />);
    expect(screen.getByRole("button")).toBeInTheDocument();
    expect(screen.getByText("👍")).toBeInTheDocument();
  });

  it("has correct aria-label when not liked", () => {
    render(<ReactionButton trackId="track-1" />);
    expect(screen.getByLabelText("いいね")).toBeInTheDocument();
  });

  it("shows count when available", async () => {
    render(<ReactionButton trackId="track-1" />);
    expect(await screen.findByText("5")).toBeInTheDocument();
  });

  it("calls addReaction on click and updates count", async () => {
    render(<ReactionButton trackId="track-1" />);
    await screen.findByText("5");

    fireEvent.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(addReaction).toHaveBeenCalledWith("track-1", expect.any(String));
      expect(screen.getByText("6")).toBeInTheDocument();
    });
  });

  it("switches aria-label to いいね解除 after liking", async () => {
    render(<ReactionButton trackId="track-1" />);
    await screen.findByText("5");

    fireEvent.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(screen.getByLabelText("いいね解除")).toBeInTheDocument();
    });
  });

  it("calls removeReaction when already liked", async () => {
    vi.mocked(getReaction).mockResolvedValueOnce({ count: 3, user_reacted: true });
    render(<ReactionButton trackId="track-2" />);

    await waitFor(() => {
      expect(screen.getByLabelText("いいね解除")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(removeReaction).toHaveBeenCalledWith("track-2", expect.any(String));
    });
  });

  it("disables button during loading", async () => {
    let resolveAdd: (value: { ok: boolean; count: number }) => void;
    vi.mocked(addReaction).mockImplementationOnce(
      () => new Promise((resolve) => { resolveAdd = resolve; }),
    );

    render(<ReactionButton trackId="track-1" />);
    await screen.findByText("5");

    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("button")).toBeDisabled();

    resolveAdd!({ ok: true, count: 6 });
    await waitFor(() => {
      expect(screen.getByRole("button")).not.toBeDisabled();
    });
  });

  it("hides count when zero", async () => {
    vi.mocked(getReaction).mockResolvedValueOnce({ count: 0, user_reacted: false });
    render(<ReactionButton trackId="track-3" />);

    await waitFor(() => {
      expect(screen.getByLabelText("いいね")).toBeInTheDocument();
    });
    expect(screen.queryByText("0")).toBeNull();
  });
});
