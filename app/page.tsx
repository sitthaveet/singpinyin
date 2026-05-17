import fs from 'fs';
import path from 'path';
import SongList from './components/SongList';

export default function Home() {
  const lyricsDir = path.join(process.cwd(), 'lyrics');
  const songs = fs
    .readdirSync(lyricsDir)
    .filter((f) => f.endsWith('.json'))
    .map((file) => {
      const { key, title, artist } = JSON.parse(
        fs.readFileSync(path.join(lyricsDir, file), 'utf-8')
      );
      return { id: key as string, title, artist };
    });

  return (
    <div className="page-root">
      <div className="grain" aria-hidden />
      <main className="container">
        <header className="site-header">
          <div className="header-eyebrow">
            <span className="eyebrow-dot" />
            <span>唱拼音</span>
            <span className="eyebrow-dot" />
          </div>
          <h1 className="site-title">
            <span className="title-main">SingPinyin</span>
          </h1>
          <p className="site-subtitle">Chinese Karaoke Lyrics</p>
        </header>

        <SongList songs={songs} />
      </main>
      <footer className="site-footer">
        <div className="footer-rule" aria-hidden />
        <div className="footer-colophon">
          <span className="footer-ornament" aria-hidden>·</span>
          <p className="footer-credit">
            made with <span className="footer-heart" aria-label="love">♥</span> for China by{' '}
            <span className="footer-author">janephailin | sitthaveet</span>
          </p>
          <span className="footer-ornament" aria-hidden>·</span>
        </div>
      </footer>
    </div>
  );
}
