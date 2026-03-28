import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { describe, it, expect, afterEach, vi } from "vitest";

vi.mock("../api/client", () => ({
  searchTracks: vi.fn().mockResolvedValue({ tracks: [], total: 0, limit: 20, offset: 0 }),
}));

vi.mock("../components/AudioVisualizer", () => ({
  resumeAudioContext: vi.fn(),
}));

import { SearchBar } from "../components/SearchBar";

afterEach(cleanup);

describe("SearchBar", () => {
  const defaultProps = {
    onPlayTrack: vi.fn(),
  };

  it("renders search input", () => {
    render(<SearchBar {...defaultProps} />);
    const input = screen.getByPlaceholderText(/検索|search/i);
    expect(input).toBeDefined();
  });

  it("accepts text input", () => {
    render(<SearchBar {...defaultProps} />);
    const input = screen.getByPlaceholderText(/検索|search/i) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "jazz" } });
    expect(input.value).toBe("jazz");
  });
});
