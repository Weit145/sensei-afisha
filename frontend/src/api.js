const BASE = (import.meta.env?.VITE_API_BASE_URL || '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message, status = 0, code = '') {
    super(message);
    this.status = status;
    this.code = code;
  }
}

function errorMessage(data, status) {
  const detail = data?.detail;
  const code = detail?.error?.code;
  if (code === 'review_already_exists') return 'Вы уже оставили отзыв на этот концерт. Можно изменить свой отзыв.';
  if (code === 'USERNAME_ALREADY_EXISTS') return 'Это имя пользователя уже занято.';
  if (status === 401) return 'Ключ доступа недействителен или истёк. Войдите снова.';
  if (status === 403) return 'Недостаточно прав для этого действия.';
  if (typeof detail?.error?.message === 'string') return detail.error.message;
  if (status === 422) return 'Проверьте введённые данные.';
  if (status === 404) return 'Запись не найдена. Возможно, она была удалена.';
  if (status === 409) return 'Такая запись уже существует.';
  if (status >= 500) return 'Сервис временно недоступен. Попробуйте ещё раз.';
  return typeof detail === 'string' ? detail : 'Не удалось выполнить запрос. Попробуйте ещё раз.';
}

export async function request(path, { token, signal, body, ...options } = {}) {
  let response;
  try {
    response = await fetch(`${BASE}/api${path}`, {
      ...options,
      signal: AbortSignal.any([AbortSignal.timeout(15000), ...(signal ? [signal] : [])]),
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError('Не удалось связаться с клубом. Проверьте подключение и попробуйте ещё раз.');
  }
  if (response.ok && response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && token) globalThis.window?.dispatchEvent(new Event('session-expired'));
    throw new ApiError(errorMessage(data, response.status), response.status, data?.detail?.error?.code);
  }
  if (data === null) throw new ApiError('Сервис вернул неожиданный ответ. Попробуйте позже.');
  return data;
}

const concertPath = id => `/afisha/${encodeURIComponent(id)}`;
const reviewsPath = id => `${concertPath(id)}/reviews`;

export const api = {
  concerts: (page = 1, signal) => request(`/afisha?page=${page}&page_size=6`, { signal }),
  concert: (id, signal) => request(concertPath(id), { signal }),
  venue: (id, signal) => request(`/venues/${encodeURIComponent(id)}`, { signal }),
  messages(id, { before, signal } = {}) {
    const params = new URLSearchParams({ limit: '50' });
    if (before) params.set('before', before);
    return request(`${concertPath(id)}/messages?${params}`, { signal });
  },
  sendMessage: (id, text, token) => request(`${concertPath(id)}/messages`, { method: 'POST', body: { text }, token }),
  reviews: (id, offset = 0, signal) => request(`${reviewsPath(id)}?limit=10&offset=${offset}`, { signal }),
  reviewStats: (ids, signal) => request('/reviews/stats/batch', { method: 'POST', body: { afisha_ids: ids }, signal }),
  createReview: (id, review, token) => request(reviewsPath(id), { method: 'POST', body: review, token }),
  updateReview: (id, reviewId, review, token) => request(`${reviewsPath(id)}/${encodeURIComponent(reviewId)}`, { method: 'PATCH', body: review, token }),
  deleteReview: (id, reviewId, token) => request(`${reviewsPath(id)}/${encodeURIComponent(reviewId)}`, { method: 'DELETE', token }),
  register: (username, password) => request('/auth/register', { method: 'POST', body: { username, password } }),
};

export function mediaUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith('/') && !path.startsWith('//')) return `${BASE}${path}`;
  return '';
}
