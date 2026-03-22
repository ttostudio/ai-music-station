import { useState } from "react";
import { createRequest } from "../api/client";

interface Props {
  channelSlug: string;
}

export function RequestForm({ channelSlug }: Props) {
  const [caption, setCaption] = useState("");
  const [lyrics, setLyrics] = useState("");
  const [mood, setMood] = useState("");
  const [bpm, setBpm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const useMood = mood.trim().length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setSuccess(null);
    setError(null);

    try {
      const body: Record<string, unknown> = {};
      if (useMood) {
        body.mood = mood.trim();
      } else {
        if (caption.trim()) body.caption = caption.trim();
        if (lyrics.trim()) body.lyrics = lyrics.trim();
      }
      if (bpm) body.bpm = parseInt(bpm, 10);

      const result = await createRequest(channelSlug, body);
      setSuccess(`リクエストを送信しました！ 待ち順: #${result.position}`);
      setCaption("");
      setLyrics("");
      setMood("");
      setBpm("");
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "リクエストの送信に失敗しました",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="glass-card p-5 space-y-4"
    >
      <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
        トラックをリクエスト
      </div>

      <textarea
        value={mood}
        onChange={(e) => setMood(e.target.value)}
        placeholder="雰囲気（例: 夕焼けの帰り道、ノスタルジック）"
        rows={2}
        className="w-full input-glass px-4 py-3 text-sm resize-none"
      />

      {!useMood && (
        <>
          <input
            type="text"
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            placeholder="作りたい音楽を説明してください..."
            className="w-full input-glass px-4 py-3 text-sm"
          />

          <textarea
            value={lyrics}
            onChange={(e) => setLyrics(e.target.value)}
            placeholder="歌詞（任意、[Verse], [Chorus] タグ使用可）"
            rows={3}
            className="w-full input-glass px-4 py-3 text-sm resize-none"
          />
        </>
      )}

      {useMood && (
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
          雰囲気を指定すると、説明・歌詞フィールドは無効になります
        </p>
      )}

      <div className="flex gap-3 items-end">
        <div>
          <label className="text-xs block mb-1.5" style={{ color: 'var(--text-secondary)' }}>BPM</label>
          <input
            type="number"
            value={bpm}
            onChange={(e) => setBpm(e.target.value)}
            placeholder="自動"
            min={30}
            max={300}
            className="w-20 input-glass px-3 py-2 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all duration-300 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 hover:shadow-lg hover:shadow-indigo-500/25 disabled:opacity-50 disabled:hover:shadow-none"
        >
          {submitting ? "送信中..." : "リクエスト送信"}
        </button>
      </div>

      {success && (
        <div className="text-sm px-3 py-2 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400">
          {success}
        </div>
      )}
      {error && (
        <div className="text-sm px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
          {error}
        </div>
      )}
    </form>
  );
}
