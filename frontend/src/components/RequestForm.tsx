import { useState } from "react";
import { createRequest } from "../api/client";

interface Props {
  channelSlug: string;
}

export function RequestForm({ channelSlug }: Props) {
  const [caption, setCaption] = useState("");
  const [lyrics, setLyrics] = useState("");
  const [bpm, setBpm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setSuccess(null);
    setError(null);

    try {
      const body: Record<string, unknown> = {};
      if (caption.trim()) body.caption = caption.trim();
      if (lyrics.trim()) body.lyrics = lyrics.trim();
      if (bpm) body.bpm = parseInt(bpm, 10);

      const result = await createRequest(channelSlug, body);
      setSuccess(`リクエストを送信しました！ 待ち順: #${result.position}`);
      setCaption("");
      setLyrics("");
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
      className="bg-gray-800 rounded-lg p-4 space-y-3"
    >
      <div className="text-sm font-medium text-gray-300">
        トラックをリクエスト
      </div>

      <input
        type="text"
        value={caption}
        onChange={(e) => setCaption(e.target.value)}
        placeholder="作りたい音楽を説明してください..."
        className="w-full bg-gray-700 rounded px-3 py-2 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />

      <textarea
        value={lyrics}
        onChange={(e) => setLyrics(e.target.value)}
        placeholder="歌詞（任意、[Verse], [Chorus] タグ使用可）"
        rows={3}
        className="w-full bg-gray-700 rounded px-3 py-2 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
      />

      <div className="flex gap-3 items-end">
        <div>
          <label className="text-xs text-gray-400 block mb-1">BPM</label>
          <input
            type="number"
            value={bpm}
            onChange={(e) => setBpm(e.target.value)}
            placeholder="自動"
            min={30}
            max={300}
            className="w-20 bg-gray-700 rounded px-2 py-1.5 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-600 rounded text-sm font-medium transition-colors"
        >
          {submitting ? "送信中..." : "リクエスト送信"}
        </button>
      </div>

      {success && <div className="text-green-400 text-sm">{success}</div>}
      {error && <div className="text-red-400 text-sm">{error}</div>}
    </form>
  );
}
