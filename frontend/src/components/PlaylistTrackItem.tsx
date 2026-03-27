import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2 } from "lucide-react";
import type { PlaylistTrackEntry } from "../api/types";

interface Props {
  entry: PlaylistTrackEntry;
  index: number;
  onRemove: () => void;
}

function formatDuration(ms: number | null): string {
  if (!ms) return "--:--";
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

export function PlaylistTrackItem({ entry, index, onRemove }: Props) {
  const { track } = entry;
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: track.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`playlist-track-item ${isDragging ? "playlist-track-item-dragging" : ""}`}
    >
      <button
        className="playlist-track-handle"
        aria-label="並び替え"
        {...attributes}
        {...listeners}
      >
        <GripVertical size={16} />
      </button>

      <div className="playlist-track-num">{index + 1}</div>

      <div className="playlist-track-info">
        <div className="playlist-track-title">
          {track.caption ?? track.title ?? "（タイトルなし）"}
        </div>
        <div className="playlist-track-meta">
          {track.mood ?? "—"} · {formatDuration(track.duration_ms)}
        </div>
      </div>

      <button
        className="playlist-track-remove"
        onClick={onRemove}
        aria-label="トラックを削除"
      >
        <Trash2 size={16} />
      </button>
    </div>
  );
}
