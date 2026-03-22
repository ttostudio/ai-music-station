import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { ConfirmDialog } from "../components/ConfirmDialog";

afterEach(cleanup);

describe("ConfirmDialog", () => {
  it("renders nothing when closed", () => {
    const { container } = render(
      <ConfirmDialog
        open={false}
        title="削除確認"
        message="本当に削除しますか？"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders dialog when open", () => {
    render(
      <ConfirmDialog
        open={true}
        title="チャンネル削除"
        message="このチャンネルを削除しますか？関連トラックは保持されます。"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(
      screen.getAllByText("チャンネル削除").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "このチャンネルを削除しますか？関連トラックは保持されます。",
      ).length,
    ).toBeGreaterThan(0);
  });

  it("calls onConfirm when delete button is clicked", () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        open={true}
        title="削除確認"
        message="削除しますか？"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    expect(onConfirm).toHaveBeenCalled();
  });

  it("calls onCancel when cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open={true}
        title="削除"
        message="削除しますか？"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />,
    );
    fireEvent.click(screen.getByText("キャンセル"));
    expect(onCancel).toHaveBeenCalled();
  });
});
