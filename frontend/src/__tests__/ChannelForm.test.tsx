import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { ChannelForm } from "../components/ChannelForm";
import type { ChannelFullResponse } from "../api/types";

afterEach(cleanup);

const mockChannel: ChannelFullResponse = {
  id: "1",
  slug: "lofi",
  name: "LoFi ビーツ",
  description: "チルなローファイ",
  mood_description: "落ち着いた雰囲気",
  is_active: true,
  default_bpm_min: 70,
  default_bpm_max: 90,
  min_duration: 180,
  max_duration: 600,
  default_key: null,
  default_instrumental: true,
  prompt_template: "lofi hip hop chill beats",
  vocal_language: null,
  auto_generate: true,
  min_stock: 5,
  max_stock: 50,
};

describe("ChannelForm", () => {
  it("renders create form with empty fields", () => {
    render(
      <ChannelForm onSubmit={vi.fn()} onCancel={vi.fn()} />,
    );
    expect(
      screen.getAllByText("新規チャンネル作成").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("作成").length).toBeGreaterThan(0);
  });

  it("renders edit form with channel data", () => {
    render(
      <ChannelForm
        channel={mockChannel}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(
      screen.getAllByText("チャンネル編集").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("更新").length).toBeGreaterThan(0);

    const slugInput = screen.getByDisplayValue("lofi");
    expect(slugInput).toBeDisabled();
  });

  it("calls onCancel when cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(
      <ChannelForm onSubmit={vi.fn()} onCancel={onCancel} />,
    );
    fireEvent.click(screen.getByText("キャンセル"));
    expect(onCancel).toHaveBeenCalled();
  });

  it("shows validation error for invalid slug", async () => {
    const onSubmit = vi.fn();
    render(
      <ChannelForm onSubmit={onSubmit} onCancel={vi.fn()} />,
    );

    // Fill in slug with invalid characters
    const slugInput = screen.getByPlaceholderText("electronic");
    fireEvent.change(slugInput, { target: { value: "INVALID!" } });

    // Fill required fields
    const nameInput = screen.getByPlaceholderText("エレクトロニカ");
    fireEvent.change(nameInput, { target: { value: "テスト" } });

    // Submit
    fireEvent.click(screen.getByText("作成"));
    expect(
      screen.getAllByText(
        "スラッグは半角英小文字・数字・ハイフンのみ使用可能です",
      ).length,
    ).toBeGreaterThan(0);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows validation error when name is empty", () => {
    const onSubmit = vi.fn();
    render(
      <ChannelForm onSubmit={onSubmit} onCancel={vi.fn()} />,
    );

    const slugInput = screen.getByPlaceholderText("electronic");
    fireEvent.change(slugInput, { target: { value: "test" } });

    fireEvent.click(screen.getByText("作成"));
    expect(
      screen.getAllByText("チャンネル名は必須です").length,
    ).toBeGreaterThan(0);
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
