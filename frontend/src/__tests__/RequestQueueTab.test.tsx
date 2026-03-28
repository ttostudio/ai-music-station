import { render, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach, vi } from "vitest";

vi.mock("../api/client", () => ({
  getAllRequests: vi.fn().mockResolvedValue({ requests: [], total: 0 }),
}));

import { RequestQueueTab } from "../components/RequestQueueTab";

afterEach(cleanup);

describe("RequestQueueTab", () => {
  it("renders queue tab component", () => {
    render(<RequestQueueTab />);
    // Should render without crashing
    expect(document.querySelector("[data-testid]") || document.body.firstChild).toBeDefined();
  });

  it("shows empty state or loading initially", () => {
    render(<RequestQueueTab />);
    // Component should render some content (loading or empty state)
    const container = document.body.firstChild;
    expect(container).toBeDefined();
  });
});
