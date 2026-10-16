const BASE = (import.meta.env?.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const DEMO = import.meta.env?.VITE_DEMO_MODE === 'true';

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.status = status;
  }
}

function errorMessage(data, status) {
  if (status === 401 || status === 403) return 'Ключ доступа недействителен или истёк. Подключитесь заново.';
  if (status === 409) return 'Это имя уже занято. Попробуйте другое.';
  if (status === 404) return 'Концерт не найден. Возможно, его удалили из афиши.';
  if (status === 422) return 'Проверьте введённые данные.';
  const detail = data?.detail;
  return typeof detail === 'string' && status < 500 ? detail : 'Не удалось выполнить запрос. Попробуйте ещё раз.';
}

export async function request(path, { token, signal, body, ...options } = {}) {
  if (DEMO) {
    if (signal?.aborted) throw signal.reason;
    const { demoRequest } = await import('./demo.js');
    return demoRequest(path, options.method || 'GET');
  }
  let response;
  try {
    response = await fetch(`${BASE}/api${path}`, {
      ...options,
      signal: AbortSignal.any([AbortSignal.timeout(15000), ...(signal ? [signal] : [])]),
      headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError('Не удалось связаться с клубом. Проверьте подключение и попробуйте ещё раз.');
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) window.dispatchEvent(new Event('session-expired'));
    throw new ApiError(errorMessage(data, response.status), response.status);
  }
  if (data === null) throw new ApiError('Сервис вернул неожиданный ответ. Попробуйте позже.');
  return data;
}

export const api = {
  async concerts(signal) {
    const items = [];
    let page = 1;
    while (true) {
      const data = await request(`/afisha?page=${page}&page_size=100`, { signal });
      if (!Array.isArray(data.items)) throw new ApiError('Не удалось прочитать афишу.');
      items.push(...data.items);
      if (items.length >= data.total || data.items.length === 0) return items;
      page += 1;
    }
  },
  concert: (id, signal) => request(`/afisha/${encodeURIComponent(id)}`, { signal }),
  venue: (id, signal) => request(`/venues/${encodeURIComponent(id)}`, { signal }),
  messages: (id, signal) => request(`/afisha/${encodeURIComponent(id)}/messages`, { signal }),
  sendMessage: (id, text, token) => request(`/afisha/${encodeURIComponent(id)}/messages`, { method: 'POST', body: { text }, token }),
  register: (username, password) => request('/auth/register', { method: 'POST', body: { username, password } }),
};

export function mediaUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith('/') && !path.startsWith('//')) return `${BASE}${path}`;
  return '';
}
