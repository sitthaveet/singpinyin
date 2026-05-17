'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';

interface Song {
  id: string;
  title: string;
  artist: string;
}

export default function SongList({ songs }: { songs: Song[] }) {
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return songs;
    return songs.filter(
      (s) =>
        s.title.toLowerCase().includes(q) ||
        s.artist.toLowerCase().includes(q)
    );
  }, [query, songs]);

  return (
    <div className="song-list-wrapper">
      <div className="search-container">
        <div className="search-icon">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.5" />
            <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search songs or artists…"
          className="search-input"
          aria-label="Search songs"
        />
        {query && (
          <button
            className="search-clear"
            onClick={() => setQuery('')}
            aria-label="Clear search"
          >
            ×
          </button>
        )}
      </div>

      <div className="results-meta">
        <span className="results-count">
          {filtered.length === songs.length
            ? `${songs.length} songs`
            : `${filtered.length} of ${songs.length}`}
        </span>
        {query && filtered.length === 0 && (
          <span className="results-empty">No matches found</span>
        )}
      </div>

      <div className="song-list" role="list">
        {filtered.map((song, i) => (
          <Link
            key={`${song.id}-${i}`}
            href={`/${song.id}`}
            className="song-row"
            role="listitem"
          >
            <span className="song-index">{String(i + 1).padStart(2, '0')}</span>
            <div className="song-info">
              <span className="song-name">{song.title}</span>
              <span className="song-artist">{song.artist}</span>
            </div>
            <span className="song-arrow" aria-hidden>→</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
