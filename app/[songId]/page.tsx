import fs from 'fs';
import path from 'path';
import Link from 'next/link';
import { notFound } from 'next/navigation';

interface LyricLine {
  chinese: string;
  pinyin: string;
  type: 'lyric' | 'chinese-only' | 'blank';
}

interface SongData {
  key: string;
  title: string;
  artist: string;
  lines: LyricLine[];
}

export async function generateStaticParams() {
  const lyricsDir = path.join(process.cwd(), 'lyrics');
  return fs
    .readdirSync(lyricsDir)
    .filter((f) => f.endsWith('.json'))
    .map((file) => ({ songId: file.replace('.json', '') }));
}

export async function generateMetadata({ params }: { params: Promise<{ songId: string }> }) {
  const { songId } = await params;
  const filePath = path.join(process.cwd(), 'lyrics', `${songId}.json`);
  if (!fs.existsSync(filePath)) return {};
  const { title, artist }: SongData = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  return { title: `${title} — ${artist} | SingPinyin` };
}

export default async function SongPage({ params }: { params: Promise<{ songId: string }> }) {
  const { songId } = await params;
  const filePath = path.join(process.cwd(), 'lyrics', `${songId}.json`);
  if (!fs.existsSync(filePath)) notFound();

  const song: SongData = JSON.parse(fs.readFileSync(filePath, 'utf-8'));

  return (
    <div className="page-root">
      <div className="grain" aria-hidden />
      <main className="container song-page-container">
        <Link href="/" className="back-btn" aria-label="Back to all songs">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
            <path d="M10 3L5 8L10 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span>All Songs</span>
        </Link>

        <header className="song-header">
          <p className="song-page-artist">{song.artist}</p>
          <h1 className="song-page-title">{song.title}</h1>
        </header>

        <div className="lyrics-divider" aria-hidden />

        <article className="lyrics-container" aria-label="Lyrics">
          {song.lines.map((line, i) => {
            if (line.type === 'blank') {
              return <div key={i} className="lyric-spacer" />;
            }

            const chinese = line.chinese.replace(/\/+$/, '').trim();

            if (line.type === 'lyric' && line.pinyin) {
              return (
                <div key={i} className="lyric-line">
                  <span className="lyric-pinyin">{line.pinyin}</span>
                  <span className="lyric-chinese">{chinese}</span>
                </div>
              );
            }

            return (
              <div key={i} className="lyric-line lyric-chinese-only">
                <span className="lyric-chinese">{chinese}</span>
              </div>
            );
          })}
        </article>
      </main>
    </div>
  );
}
