import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import App from "../App";

afterEach(cleanup);

describe("App", () => {
  it("renders loading state initially", () => {
    render(<App />);
    expect(
      screen.getAllByText("Loading channels...").length,
    ).toBeGreaterThan(0);
  });
});
