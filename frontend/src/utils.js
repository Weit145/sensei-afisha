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

export const averageRating = stats => stats?.reviews_count > 0 ? (stats.rating_sum / stats.reviews_count).toFixed(1) : null;

export function mergeMessages(previous, incoming) {
  const byId = new Map(previous.map(message => [message.id, message]));
  for (const message of incoming) byId.set(message.id, message);
  return [...byId.values()].sort((a, b) => new Date(a.created_at) - new Date(b.created_at) || a.id.localeCompare(b.id));
}

export const canCreateReview = (event, now = Date.now()) => event.status === 'published' && new Date(event.ends_at).getTime() <= now;
