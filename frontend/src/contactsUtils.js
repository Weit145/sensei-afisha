export function contactValue(value, field) {
  const text = (value || '').trim();
  if (!text) return null;
  const hosts = field === 'tg_url' ? ['t.me', 'telegram.me'] : ['vk.ru', 'vk.com'];
  const authority = text.match(/^https:\/\/([^/?#]+)\//i)?.[1]?.toLowerCase();
  try {
    const url = new URL(text);
    if (text.length > 255 || url.protocol !== 'https:' || !hosts.includes(authority) || !url.pathname.replaceAll('/', '') || url.username || url.password || /\s|\\/.test(text)) throw new Error();
    return text;
  } catch { throw new Error(`Укажите HTTPS-ссылку на профиль ${field === 'tg_url' ? 't.me или telegram.me' : 'vk.ru или vk.com'}, до 255 символов.`); }
}

export function contactsPayload(form) {
  const body = {}, errors = {};
  for (const field of ['tg_url', 'vk_url']) {
    try { body[field] = contactValue(form[field], field); }
    catch (error) { errors[field] = error.message; }
  }
  return { body, errors };
}
