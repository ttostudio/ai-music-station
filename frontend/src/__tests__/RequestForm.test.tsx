import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import { RequestForm } from "../components/RequestForm";

afterEach(cleanup);

describe("RequestForm", () => {
  it("renders form fields", () => {
    render(<RequestForm channelSlug="lofi" />);
    expect(
      screen.getAllByPlaceholderText(/作りたい音楽を説明/).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByPlaceholderText(/歌詞/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("リクエスト送信").length).toBeGreaterThan(0);
  });

  it("has BPM input", () => {
    render(<RequestForm channelSlug="lofi" />);
    expect(screen.getAllByPlaceholderText("自動").length).toBeGreaterThan(0);
  });

  it("submit button is enabled", () => {
    render(<RequestForm channelSlug="lofi" />);
    const btns = screen.getAllByText("リクエスト送信");
    expect(btns[0]).not.toBeDisabled();
  });
});
