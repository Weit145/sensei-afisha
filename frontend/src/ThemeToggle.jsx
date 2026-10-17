import { useEffect, useState } from 'react';
import { Icon } from './components.jsx';

const THEME_KEY = 'musical-monday:theme';

export default function ThemeToggle() {
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || 'light');
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#1c1b1f' : '#782b38');
  }, [theme]);

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const sync = () => {
      let saved;
      try { saved = localStorage.getItem(THEME_KEY); } catch {}
      setTheme(saved === 'light' || saved === 'dark' ? saved : media.matches ? 'dark' : 'light');
    };
    const storage = event => { if (event.key === THEME_KEY || event.key === null) sync(); };
    media.addEventListener('change', sync);
    window.addEventListener('storage', storage);
    return () => { media.removeEventListener('change', sync); window.removeEventListener('storage', storage); };
  }, []);

  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    try { localStorage.setItem(THEME_KEY, next); } catch { /* Keep the choice for this visit if storage is unavailable. */ }
  }

  return <button type="button" className="icon-button theme-toggle" onClick={toggle} aria-label={theme === 'dark' ? 'Включить светлую тему' : 'Включить тёмную тему'} title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}><Icon name={theme === 'dark' ? 'sun' : 'moon'} size={20} /></button>;
}
