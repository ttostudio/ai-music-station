import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import { QualityScoreBadge } from "../components/QualityScoreBadge";

afterEach(cleanup);

describe("QualityScoreBadge", () => {
  describe("グレード分類", () => {
    it("スコア≥80のときグレードA（非常に良好）を表示する", () => {
      render(<QualityScoreBadge score={85} />);
      expect(screen.getByText("非常に良好")).toBeTruthy();
    });

    it("スコア≥60かつ<80のときグレードB（良好）を表示する", () => {
      render(<QualityScoreBadge score={70} />);
      expect(screen.getByText("良好")).toBeTruthy();
    });

    it("スコア≥40かつ<60のときグレードC（可）を表示する", () => {
      render(<QualityScoreBadge score={50} />);
      expect(screen.getByText("可")).toBeTruthy();
    });

    it("スコア<40のときグレードD（低品質）を表示する", () => {
      render(<QualityScoreBadge score={25} />);
      expect(screen.getByText("低品質")).toBeTruthy();
    });
  });

  describe("境界値", () => {
    it("スコア=80はグレードA", () => {
      render(<QualityScoreBadge score={80} />);
      expect(screen.getByText("非常に良好")).toBeTruthy();
    });

    it("スコア=60はグレードB", () => {
      render(<QualityScoreBadge score={60} />);
      expect(screen.getByText("良好")).toBeTruthy();
    });

    it("スコア=40はグレードC", () => {
      render(<QualityScoreBadge score={40} />);
      expect(screen.getByText("可")).toBeTruthy();
    });

    it("スコア=39はグレードD", () => {
      render(<QualityScoreBadge score={39} />);
      expect(screen.getByText("低品質")).toBeTruthy();
    });

    it("スコア=0はグレードD", () => {
      render(<QualityScoreBadge score={0} />);
      expect(screen.getByText("低品質")).toBeTruthy();
    });

    it("スコア=100はグレードA", () => {
      render(<QualityScoreBadge score={100} />);
      expect(screen.getByText("非常に良好")).toBeTruthy();
    });
  });

  describe("スコア数値表示", () => {
    it("スコアを整数で表示する", () => {
      render(<QualityScoreBadge score={87.6} />);
      expect(screen.getByText(/88/)).toBeTruthy();
    });
  });

  describe("showLabel prop", () => {
    it("showLabel=falseのときラベルを非表示にする", () => {
      render(<QualityScoreBadge score={85} showLabel={false} />);
      expect(screen.queryByText("非常に良好")).toBeNull();
    });

    it("showLabel=true（デフォルト）のときラベルを表示する", () => {
      render(<QualityScoreBadge score={70} />);
      expect(screen.getByText("良好")).toBeTruthy();
    });
  });

  describe("アクセシビリティ", () => {
    it("aria-labelにスコアとラベルを含む", () => {
      render(<QualityScoreBadge score={87} />);
      const badge = screen.getByRole("status");
      expect(badge.getAttribute("aria-label")).toContain("87");
      expect(badge.getAttribute("aria-label")).toContain("非常に良好");
    });

    it("グレードDにaria-labelが警告を含む", () => {
      render(<QualityScoreBadge score={20} />);
      const badge = screen.getByRole("status");
      expect(badge.getAttribute("aria-label")).toContain("20");
      expect(badge.getAttribute("aria-label")).toContain("低品質");
    });
  });
});
