import { useState, useEffect } from "react";
import { X } from "lucide-react";
import type { Playlist } from "../api/types";

interface Props {
  /** null = 作成モード、Playlist = 編集モード */
  playlist?: Playlist | null;
  onSave: (name: string, description: string) => Promise<void>;
  onClose: () => void;
}

const NAME_MAX = 50;
const DESC_MAX = 200;

export function PlaylistCreateModal({ playlist, onSave, onClose }: Props) {
  const [name, setName] = useState(playlist?.name ?? "");
  const [description, setDescription] = useState(
    playlist?.description ?? "",
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setName(playlist?.name ?? "");
    setDescription(playlist?.description ?? "");
  }, [playlist]);

  const isEdit = Boolean(playlist);
  const canSave = name.trim().length > 0 && name.length <= NAME_MAX && !saving;

  async function handleSave() {
    if (!canSave) return;
    setSaving(true);
    setError(null);
    try {
      await onSave(name.trim(), description.trim());
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存に失敗しました");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="modal-header">
          <h2 id="modal-title" className="modal-title">
            {isEdit ? "プレイリストを編集" : "プレイリストを作成"}
          </h2>
          <button className="modal-close" onClick={onClose} aria-label="閉じる">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <div className="modal-field">
            <label className="modal-label" htmlFor="playlist-name">
              名前 <span className="modal-required">*</span>
            </label>
            <div className="modal-input-wrap">
              <input
                id="playlist-name"
                className="modal-input"
                type="text"
                placeholder="プレイリスト名"
                value={name}
                maxLength={NAME_MAX}
                onChange={(e) => setName(e.target.value)}
              />
              <span className="modal-counter">
                {name.length}/{NAME_MAX}
              </span>
            </div>
          </div>

          <div className="modal-field">
            <label className="modal-label" htmlFor="playlist-desc">
              説明（任意）
            </label>
            <div className="modal-input-wrap">
              <textarea
                id="playlist-desc"
                className="modal-textarea"
                placeholder="説明を入力..."
                value={description}
                maxLength={DESC_MAX}
                onChange={(e) => setDescription(e.target.value)}
              />
              <span className="modal-counter">
                {description.length}/{DESC_MAX}
              </span>
            </div>
          </div>

          {error && <div className="modal-error">{error}</div>}
        </div>

        <div className="modal-footer">
          <button className="modal-btn-cancel" onClick={onClose}>
            キャンセル
          </button>
          <button
            className="modal-btn-save"
            onClick={handleSave}
            disabled={!canSave}
            aria-disabled={!canSave}
          >
            {saving ? "保存中..." : isEdit ? "保存する" : "作成する"}
          </button>
        </div>
      </div>
    </div>
  );
}
