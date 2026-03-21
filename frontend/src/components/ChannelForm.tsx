import { useState, useEffect } from "react";
import type { ChannelCreateBody, ChannelFullResponse } from "../api/types";

interface ChannelFormProps {
  channel?: ChannelFullResponse | null;
  onSubmit: (body: ChannelCreateBody) => Promise<void>;
  onCancel: () => void;
}

const INITIAL_VALUES: ChannelCreateBody = {
  slug: "",
  name: "",
  description: "",
  mood_description: null,
  default_bpm_min: 80,
  default_bpm_max: 120,
  default_duration: 180,
  default_key: null,
  default_instrumental: true,
  prompt_template: "",
  vocal_language: null,
  auto_generate: true,
  min_stock: 5,
  max_stock: 50,
};

export function ChannelForm({ channel, onSubmit, onCancel }: ChannelFormProps) {
  const isEdit = !!channel;
  const [form, setForm] = useState<ChannelCreateBody>(INITIAL_VALUES);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (channel) {
      setForm({
        slug: channel.slug,
        name: channel.name,
        description: channel.description ?? "",
        mood_description: channel.mood_description,
        default_bpm_min: channel.default_bpm_min,
        default_bpm_max: channel.default_bpm_max,
        default_duration: channel.default_duration,
        default_key: channel.default_key,
        default_instrumental: channel.default_instrumental,
        prompt_template: channel.prompt_template,
        vocal_language: channel.vocal_language,
        auto_generate: channel.auto_generate,
        min_stock: channel.min_stock,
        max_stock: channel.max_stock,
      });
    } else {
      setForm(INITIAL_VALUES);
    }
  }, [channel]);

  function update<K extends keyof ChannelCreateBody>(
    key: K,
    value: ChannelCreateBody[K],
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!form.slug || !/^[a-z0-9-]+$/.test(form.slug)) {
      setError("スラッグは半角英小文字・数字・ハイフンのみ使用可能です");
      return;
    }
    if (!form.name.trim()) {
      setError("チャンネル名は必須です");
      return;
    }
    if (!form.prompt_template.trim()) {
      setError("プロンプトテンプレートは必須です");
      return;
    }
    if ((form.default_bpm_min ?? 80) >= (form.default_bpm_max ?? 120)) {
      setError("BPM最小値は最大値より小さくしてください");
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit(form);
    } catch (err) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-lg font-bold text-white">
        {isEdit ? "チャンネル編集" : "新規チャンネル作成"}
      </h3>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="grid grid-cols-2 gap-3">
        <label className="block col-span-2 sm:col-span-1">
          <span className="text-gray-300 text-sm">スラッグ</span>
          <input
            type="text"
            value={form.slug}
            onChange={(e) => update("slug", e.target.value)}
            disabled={isEdit}
            placeholder="electronic"
            className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white disabled:opacity-50"
          />
        </label>

        <label className="block col-span-2 sm:col-span-1">
          <span className="text-gray-300 text-sm">チャンネル名</span>
          <input
            type="text"
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
            placeholder="エレクトロニカ"
            className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
          />
        </label>
      </div>

      <label className="block">
        <span className="text-gray-300 text-sm">説明</span>
        <input
          type="text"
          value={form.description ?? ""}
          onChange={(e) => update("description", e.target.value)}
          className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
        />
      </label>

      <label className="block">
        <span className="text-gray-300 text-sm">雰囲気の説明</span>
        <input
          type="text"
          value={form.mood_description ?? ""}
          onChange={(e) =>
            update("mood_description", e.target.value || null)
          }
          className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
        />
      </label>

      <div className="grid grid-cols-3 gap-3">
        <label className="block">
          <span className="text-gray-300 text-sm">BPM最小</span>
          <input
            type="number"
            value={form.default_bpm_min ?? 80}
            onChange={(e) => update("default_bpm_min", Number(e.target.value))}
            min={30}
            max={300}
            className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
          />
        </label>
        <label className="block">
          <span className="text-gray-300 text-sm">BPM最大</span>
          <input
            type="number"
            value={form.default_bpm_max ?? 120}
            onChange={(e) => update("default_bpm_max", Number(e.target.value))}
            min={30}
            max={300}
            className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
          />
        </label>
        <label className="block">
          <span className="text-gray-300 text-sm">再生時間(秒)</span>
          <input
            type="number"
            value={form.default_duration ?? 180}
            onChange={(e) => update("default_duration", Number(e.target.value))}
            min={10}
            max={600}
            className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
          />
        </label>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="text-gray-300 text-sm">デフォルトキー</span>
          <input
            type="text"
            value={form.default_key ?? ""}
            onChange={(e) => update("default_key", e.target.value || null)}
            placeholder="Cm"
            className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
          />
        </label>
        <label className="block">
          <span className="text-gray-300 text-sm">ボーカル言語</span>
          <input
            type="text"
            value={form.vocal_language ?? ""}
            onChange={(e) =>
              update("vocal_language", e.target.value || null)
            }
            placeholder="ja"
            className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
          />
        </label>
      </div>

      <label className="block">
        <span className="text-gray-300 text-sm">プロンプトテンプレート</span>
        <textarea
          value={form.prompt_template}
          onChange={(e) => update("prompt_template", e.target.value)}
          rows={3}
          className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
        />
      </label>

      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="text-gray-300 text-sm">最小ストック</span>
          <input
            type="number"
            value={form.min_stock ?? 5}
            onChange={(e) => update("min_stock", Number(e.target.value))}
            min={0}
            max={100}
            className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
          />
        </label>
        <label className="block">
          <span className="text-gray-300 text-sm">最大ストック</span>
          <input
            type="number"
            value={form.max_stock ?? 50}
            onChange={(e) => update("max_stock", Number(e.target.value))}
            min={1}
            max={500}
            className="w-full mt-1 px-3 py-2 bg-gray-700 rounded text-white"
          />
        </label>
      </div>

      <div className="flex gap-4">
        <label className="flex items-center gap-2 text-gray-300">
          <input
            type="checkbox"
            checked={form.default_instrumental ?? true}
            onChange={(e) => update("default_instrumental", e.target.checked)}
            className="rounded"
          />
          インストゥルメンタル
        </label>
        <label className="flex items-center gap-2 text-gray-300">
          <input
            type="checkbox"
            checked={form.auto_generate ?? true}
            onChange={(e) => update("auto_generate", e.target.checked)}
            className="rounded"
          />
          自動生成
        </label>
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded bg-gray-600 text-white hover:bg-gray-500"
        >
          キャンセル
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {submitting ? "保存中..." : isEdit ? "更新" : "作成"}
        </button>
      </div>
    </form>
  );
}
