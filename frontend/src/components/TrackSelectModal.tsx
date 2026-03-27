import { useState, useEffect } from "react";
import { X, Search } from "lucide-react";
import type { Track } from "../api/types";

interface Props {
  existingTrackIds: Set<string>;
  onAdd: (trackIds: string[]) => Promise<void>;
  onClose: () => void;
  fetchTracks: () => Promise<Track[]>;
}

function formatDuration(ms: number | null): string {
  if (!ms) return "--:--";
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

export function TrackSelectModal({
  existingTrackIds,
  onAdd,
  onClose,
  fetchTracks,
}: Props) {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchTracks()
      .then((t) => {
        if (!cancelled) setTracks(t);
      })
      .catch(() => {
        if (!cancelled) setError("トラックの読み込みに失敗しました");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [fetchTracks]);

  const filtered = tracks.filter((t) => {
    const q = query.toLowerCase();
    return (
      (t.caption ?? "").toLowerCase().includes(q) ||
      (t.title ?? "").toLowerCase().includes(q) ||
      (t.mood ?? "").toLowerCase().includes(q)
    );
  });

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  async function handleAdd() {
    if (selected.size === 0) return;
    setSaving(true);
    setError(null);
    try {
      await onAdd(Array.from(selected));
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "追加に失敗しました");
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
        className="modal-panel modal-panel-lg"
        role="dialog"
        aria-modal="true"
        aria-labelledby="track-modal-title"
      >
        <div className="modal-header">
          <h2 id="track-modal-title" className="modal-title">
            トラックを追加
          </h2>
          <button className="modal-close" onClick={onClose} aria-label="閉じる">
            <X size={18} />
          </button>
        </div>

        <div className="modal-search-wrap">
          <Search size={16} className="modal-search-icon" />
          <input
            className="modal-search-input"
            type="text"
            placeholder="トラックを検索..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div className="track-select-list">
          {loading && (
            <div className="track-select-empty">読み込み中...</div>
          )}
          {!loading && filtered.length === 0 && (
            <div className="track-select-empty">
              トラックが見つかりません
            </div>
          )}
          {!loading &&
            filtered.map((track) => {
              const alreadyAdded = existingTrackIds.has(track.id);
              const isSelected = selected.has(track.id);
              return (
                <div
                  key={track.id}
                  className={`track-select-row ${alreadyAdded ? "track-select-row-disabled" : ""} ${isSelected ? "track-select-row-selected" : ""}`}
                  onClick={() => !alreadyAdded && toggleSelect(track.id)}
                  role="checkbox"
                  aria-checked={isSelected}
                  aria-label={`${track.caption ?? track.title ?? "トラック"}を選択`}
                  tabIndex={alreadyAdded ? -1 : 0}
                  onKeyDown={(e) =>
                    e.key === "Enter" && !alreadyAdded && toggleSelect(track.id)
                  }
                >
                  <div
                    className={`track-select-checkbox ${isSelected ? "track-select-checkbox-checked" : ""}`}
                  />
                  <div className="track-select-info">
                    <div className="track-select-title">
                      {track.caption ?? track.title ?? "（タイトルなし）"}
                    </div>
                    <div className="track-select-meta">
                      {track.mood ?? "—"} · {formatDuration(track.duration_ms)}
                    </div>
                  </div>
                  {alreadyAdded && (
                    <span className="track-select-badge">追加済み</span>
                  )}
                </div>
              );
            })}
        </div>

        {error && <div className="modal-error modal-error-pad">{error}</div>}

        <div className="modal-footer">
          <span className="track-select-count">
            {selected.size > 0 ? `${selected.size}件選択中` : ""}
          </span>
          <button
            className="modal-btn-save"
            onClick={handleAdd}
            disabled={selected.size === 0 || saving}
            aria-disabled={selected.size === 0 || saving}
          >
            {saving ? "追加中..." : "追加する"}
          </button>
        </div>
      </div>
    </div>
  );
}
