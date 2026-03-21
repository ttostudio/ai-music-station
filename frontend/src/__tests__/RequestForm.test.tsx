import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import { RequestForm } from "../components/RequestForm";

afterEach(cleanup);

describe("RequestForm", () => {
  it("renders form fields", () => {
    render(<RequestForm channelSlug="lofi" />);
    expect(
      screen.getAllByPlaceholderText(/Describe the music/).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByPlaceholderText(/Lyrics/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Submit Request").length).toBeGreaterThan(0);
  });

  it("has BPM input", () => {
    render(<RequestForm channelSlug="lofi" />);
    expect(screen.getAllByPlaceholderText("Auto").length).toBeGreaterThan(0);
  });

  it("submit button is enabled", () => {
    render(<RequestForm channelSlug="lofi" />);
    const btns = screen.getAllByText("Submit Request");
    expect(btns[0]).not.toBeDisabled();
  });
});
