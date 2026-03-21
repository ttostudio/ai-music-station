import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach, vi } from "vitest";
import { ReactionButton } from "../components/ReactionButton";

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
});
