import { TIMEZONE } from './utils.js';

export function moscowInput(value) {
  if (!value) return '';
  const parts = Object.fromEntries(new Intl.DateTimeFormat('sv-SE', {
    timeZone: TIMEZONE, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(new Date(value)).map(part => [part.type, part.value]));
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

export function concertPayload(form) {
  const starts = new Date(`${form.starts_at}:00+03:00`), ends = new Date(`${form.ends_at}:00+03:00`);
  if (!form.title.trim()) throw new Error('Укажите название концерта.');
  if (!Number.isFinite(starts.getTime()) || !Number.isFinite(ends.getTime())) throw new Error('Укажите дату и время начала и окончания.');
  if (ends <= starts) throw new Error('Окончание должно быть позже начала концерта.');
  if (!form.venue_ids.length) throw new Error('Выберите хотя бы одну площадку.');
  if (!['published', 'cancelled'].includes(form.status)) throw new Error('Выберите статус концерта.');
  const age = form.age_limit === '' ? null : Number(form.age_limit);
  if (age !== null && ![0, 6, 12, 16, 18].includes(age)) throw new Error('Выберите возрастное ограничение: 0+, 6+, 12+, 16+ или 18+.');
  return {
    title: form.title.trim(), short_description: form.short_description.trim() || null,
    description: form.description.trim() || null, starts_at: starts.toISOString(), ends_at: ends.toISOString(),
    venue_ids: form.venue_ids, age_limit: age, status: form.status,
  };
}

export function venuePayload(form) {
  const result = {};
  for (const [field, label, max] of [['name', 'название площадки', 255], ['city', 'город', 100], ['address', 'адрес', 500]]) {
    result[field] = form[field].trim();
    if (!result[field] || result[field].length > max) throw new Error(`Укажите ${label} (до ${max} символов).`);
  }
  for (const [field, label, max] of [['latitude', 'Широта', 90], ['longitude', 'Долгота', 180]]) {
    result[field] = form[field] === '' ? null : Number(form[field]);
    if (result[field] !== null && (!Number.isFinite(result[field]) || Math.abs(result[field]) > max)) throw new Error(`${label}: допустимое значение от −${max} до ${max}.`);
  }
  return result;
}

// Match the signatures accepted by the running backend, rather than trusting a filename.
export async function validateImages(files) {
  for (const file of files) {
    const bytes = new Uint8Array(await file.slice(0, 16).arrayBuffer());
    const matches = (...signature) => signature.every((value, index) => bytes[index] === value);
    const text = new TextDecoder().decode(bytes);
    if (!(matches(255, 216, 255) || matches(137, 80, 78, 71, 13, 10, 26, 10) || text.startsWith('GIF87a') || text.startsWith('GIF89a') || (text.startsWith('RIFF') && text.slice(8, 12) === 'WEBP'))) {
      throw new Error(`«${file.name}»: поддерживаются только JPEG, PNG, GIF и WebP.`);
    }
  }
}
