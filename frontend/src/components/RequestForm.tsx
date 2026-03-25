import { useState } from "react";
import { submitGenerate } from "../api/client";
import type { Channel } from "../api/types";
import { RequestHistory } from "./RequestHistory";

type Mood = "cheerful" | "calm" | "energetic" | "melancholy";

const MOOD_LABELS: Record<Mood, string> = {
  cheerful: "明るい",
  calm: "落ち着いた",
  energetic: "エネルギッシュ",
  melancholy: "哀愁",
};

interface Props {
  channels: Channel[];
  defaultSlug?: string;
}

export function RequestForm({ channels, defaultSlug }: Props) {
  const activeChannels = channels.filter((c) => c.is_active);
  const initialSlug = defaultSlug ?? (activeChannels[0]?.slug ?? "");

  const [channelSlug, setChannelSlug] = useState(initialSlug);
  const [mood, setMood] = useState<Mood | "">("");
  const [prompt, setPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedIds, setSubmittedIds] = useState<string[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!channelSlug) return;
    setSubmitting(true);
    setError(null);

    try {
      const body: Parameters<typeof submitGenerate>[0] = { channel_slug: channelSlug };
      if (mood) body.mood = mood;
      if (prompt.trim()) body.caption = prompt.trim();

      const result = await submitGenerate(body);
      setSubmittedIds((prev) => [result.id, ...prev]);
      setPrompt("");
      setMood("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "リクエストの送信に失敗しました",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="request-panel">
      <form onSubmit={handleSubmit} className="glass-card p-5 space-y-4">
        <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          トラックをリクエスト
        </div>

        {/* Channel selector */}
        <div>
          <label className="text-xs block mb-1.5" style={{ color: "var(--text-secondary)" }}>
            チャンネル
          </label>
          <select
            value={channelSlug}
            onChange={(e) => setChannelSlug(e.target.value)}
            className="w-full input-glass px-3 py-2 text-sm"
          >
            {activeChannels.map((ch) => (
              <option key={ch.slug} value={ch.slug}>
                {ch.name}
              </option>
            ))}
          </select>
        </div>

        {/* Mood selector */}
        <div>
          <label className="text-xs block mb-2" style={{ color: "var(--text-secondary)" }}>
            ムード（任意）
          </label>
          <div className="flex flex-wrap gap-2">
            {(Object.keys(MOOD_LABELS) as Mood[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMood((prev) => (prev === m ? "" : m))}
                className={`mood-pill ${mood === m ? "mood-pill-active" : ""}`}
              >
                {MOOD_LABELS[m]}
              </button>
            ))}
          </div>
        </div>

        {/* Optional prompt */}
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="追加の指示（任意）例: 夕焼けの帰り道、ノスタルジック"
          rows={2}
          className="w-full input-glass px-4 py-3 text-sm resize-none"
        />

        <button
          type="submit"
          disabled={submitting || !channelSlug}
          className="btn-submit w-full"
        >
          {submitting ? "送信中..." : "リクエスト送信"}
        </button>

        {error && (
          <div className="text-sm px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
            {error}
          </div>
        )}
      </form>

      {submittedIds.length > 0 && (
        <RequestHistory requestIds={submittedIds} />
      )}
    </div>
  );
}
