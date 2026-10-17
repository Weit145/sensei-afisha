import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const bootstrap = html.match(/<script id="theme-init">([\s\S]*?)<\/script>/)[1];
function initialTheme(saved, darkSystem, blockedStorage = false) {
  const root = { dataset: {}, style: {} };
  runInNewContext(bootstrap, {
    document: { documentElement: root },
    localStorage: { getItem() { if (blockedStorage) throw new Error('Storage disabled'); return saved; } },
    window: { matchMedia: () => ({ matches: darkSystem }) },
  });
  return { theme: root.dataset.theme, colorScheme: root.style.colorScheme };
}

test('saved theme overrides system preference before React and CSS load', () => {
  assert.deepEqual(initialTheme('light', true), { theme: 'light', colorScheme: 'light' });
  assert.deepEqual(initialTheme('dark', false), { theme: 'dark', colorScheme: 'dark' });
});

test('first visit and unavailable storage use the system theme without breaking startup', () => {
  assert.equal(initialTheme(null, true).theme, 'dark');
  assert.equal(initialTheme(null, false).theme, 'light');
  assert.equal(initialTheme('invalid', true).theme, 'dark');
  assert.equal(initialTheme(null, true, true).theme, 'dark');
});
