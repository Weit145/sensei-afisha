export const TIMEZONE = 'Europe/Moscow';
const dateFormat = (date, options) => new Intl.DateTimeFormat('ru-RU', { timeZone: TIMEZONE, ...options }).format(new Date(date));
export const dateLong = date => dateFormat(date, { day: 'numeric', month: 'long', year: 'numeric' });
export const dateShort = date => dateFormat(date, { day: 'numeric', month: 'long' });
export const time = date => dateFormat(date, { hour: '2-digit', minute: '2-digit' });
export const weekday = date => dateFormat(date, { weekday: 'long' });
export const monthKey = date => dateFormat(date, { year: 'numeric', month: '2-digit' });
export const monthLabel = date => dateFormat(date, { month: 'long', year: 'numeric' });
export const isPast = (event, now = Date.now()) => new Date(event.ends_at).getTime() < now;
export const participantName = id => `Слушатель ${String(id).replaceAll('-', '').slice(0, 4).toUpperCase()}`;
export const initials = name => (name || '?').slice(0, 2).toUpperCase();
export const hash = value => [...String(value)].reduce((n, char) => ((n << 5) - n + char.charCodeAt(0)) | 0, 0) >>> 0;

export function filterConcerts(events, { query = '', period = 'all', month = '', plannedIds, now = Date.now() } = {}) {
  const search = query.trim().toLocaleLowerCase('ru');
  return events.filter(event => {
    const text = [event.title, event.short_description, ...(event.venue_names || [])].join(' ').toLocaleLowerCase('ru');
    return (!search || text.includes(search))
      && (period !== 'upcoming' || !isPast(event, now))
      && (period !== 'past' || isPast(event, now))
      && (!month || monthKey(event.starts_at) === month)
      && (!plannedIds || plannedIds.includes(event.id));
  }).sort((a, b) => period === 'past'
    ? new Date(b.starts_at) - new Date(a.starts_at)
    : new Date(a.starts_at) - new Date(b.starts_at));
}

export function readStored(key, fallback, storage = 'localStorage') {
  try {
    const target = typeof storage === 'string' ? globalThis[storage] : storage;
    return JSON.parse(target.getItem(key)) ?? fallback;
  } catch { return fallback; }
}

export function writeStored(key, value, storage = 'localStorage') {
  try {
    const target = typeof storage === 'string' ? globalThis[storage] : storage;
    target.setItem(key, JSON.stringify(value));
    return true;
  } catch { return false; }
}

// Decoding supplies a display label only. The server authenticates every POST.
export function parseAccessKey(token) {
  try {
    const parts = token.trim().split('.');
    if (parts.length !== 3) return null;
    const raw = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(raw), c => c.charCodeAt(0))));
    if (!/^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i.test(payload.user_id)) return null;
    if (!['user', 'admin'].includes(payload.role) || !Number.isFinite(payload.exp) || payload.exp * 1000 <= Date.now()) return null;
    return { token: token.trim(), id: payload.user_id, expiresAt: payload.exp * 1000 };
  } catch { return null; }
}
