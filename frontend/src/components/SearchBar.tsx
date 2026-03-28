import { useState, useEffect, useRef, useCallback } from "react";
import { Search, X, Play } from "lucide-react";
import { searchTracks } from "../api/client";
import type { TrackSearchResponse, Track } from "../api/types";

interface Props {
  onPlayTrack: (track: Track) => void;
  /** モバイル向け: 展開/折りたたみ制御 */
  mobile?: boolean;
}

function toTrack(r: TrackSearchResponse): Track {
  return {
    id: r.id,
    caption: r.caption,
    title: r.title,
    mood: r.mood,
    duration_ms: r.duration_ms,
    bpm: r.bpm,
    music_key: null,
    instrumental: null,
    play_count: 0,
    like_count: 0,
    quality_score: r.quality_score,
    created_at: r.created_at,
  };
}

function formatDuration(ms: number | null): string {
  if (!ms) return "--:--";
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, "0")}`;
}

export function SearchBar({ onPlayTrack, mobile = false }: Props) {
  const [expanded, setExpanded] = useState(!mobile);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<TrackSearchResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    try {
      const res = await searchTracks(q, 10);
      setResults(res.tracks);
      setOpen(res.tracks.length > 0);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(query), 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, doSearch]);

  // Close panel when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleExpand = () => {
    setExpanded(true);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const handleClear = () => {
    setQuery("");
    setResults([]);
    setOpen(false);
    if (mobile) setExpanded(false);
  };

  const handlePlay = (r: TrackSearchResponse) => {
    onPlayTrack(toTrack(r));
    setOpen(false);
    setQuery("");
    if (mobile) setExpanded(false);
  };

  // Mobile: icon only when collapsed
  if (mobile && !expanded) {
    return (
      <button
        className="search-icon-btn"
        onClick={handleExpand}
        aria-label="検索"
      >
        <Search size={20} />
      </button>
    );
  }

  return (
    <div className="search-bar-container" ref={containerRef}>
      <div className="search-bar-input-row">
        <Search size={16} className="search-bar-icon" aria-hidden="true" />
        <input
          ref={inputRef}
          type="text"
          className="search-bar-input"
          placeholder="曲名・ムードで検索..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          aria-label="トラック検索"
          aria-expanded={open}
          aria-autocomplete="list"
          aria-controls="search-results"
        />
        {loading && <span className="search-bar-spinner" aria-hidden="true" />}
        {(query || mobile) && (
          <button className="search-bar-clear" onClick={handleClear} aria-label="クリア">
            <X size={14} />
          </button>
        )}
      </div>

      {open && (
        <div
          id="search-results"
          className="search-results-panel"
          role="listbox"
          aria-label="検索結果"
        >
          {results.map((r) => (
            <div key={r.id} className="search-result-item" role="option" aria-selected="false">
              <div className="search-result-info">
                <div className="search-result-title">{r.title || r.caption}</div>
                <div className="search-result-meta">
                  {r.mood && <span>{r.mood}</span>}
                  {r.channel_slug && <span>{r.channel_slug}</span>}
                  <span>{formatDuration(r.duration_ms)}</span>
                </div>
              </div>
              <button
                className="search-result-play"
                onClick={() => handlePlay(r)}
                aria-label={`${r.title || r.caption} を再生`}
              >
                <Play size={14} fill="currentColor" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
