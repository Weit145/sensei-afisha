const BASE = (import.meta.env?.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const DEMO = import.meta.env?.VITE_DEMO_MODE === 'true';

export class ApiError extends Error {
  constructor(message, status = 0, code = '') {
    super(message); this.name = 'ApiError'; this.status = status; this.code = code;
  }
}

function responseError(data, status, path) {
  const error = data?.detail?.error;
  const code = error?.code || '';
  let message;
  if (status === 401) message = path === '/auth/login' ? 'Неверное имя пользователя или пароль.' : 'Сессия истекла. Войдите в клуб снова.';
  else if (status === 403) message = code === 'CSRF_FAILED' ? 'Сервер отклонил источник запроса. Проверьте адрес сайта и настройки доступа API.' : 'У вас нет прав для этого действия.';
  else if (status === 409) message = code === 'USERNAME_ALREADY_EXISTS' ? 'Это имя уже занято. Попробуйте другое.' : code === 'review_already_exists' ? 'Вы уже оставили отзыв. Можно изменить свой отзыв в списке.' : 'Данные уже изменились или такая запись существует. Обновите страницу и повторите действие.';
  else if (status === 422) message = 'Проверьте обязательные поля, даты и формат введённых данных.';
  else if (status === 404) message = error?.message || 'Запись не найдена. Возможно, её уже удалили.';
  else if (status < 500) message = error?.message || (typeof data?.detail === 'string' ? data.detail : 'Не удалось выполнить действие. Проверьте данные.');
  else message = 'Сервис временно недоступен. Попробуйте ещё раз.';
  return new ApiError(message, status, code);
}

// The access token lives only in this client. Serialize rotating-cookie operations
// locally and, with Web Locks where available, between tabs of this origin.
export function createApiClient({ base = BASE, fetcher = (...args) => fetch(...args), demo = DEMO, locks = globalThis.navigator?.locks, onExpired = () => globalThis.window?.dispatchEvent(new Event('session-expired')) } = {}) {
  let token = null, user = null, generation = 0;
  let cookieQueue = Promise.resolve(), refreshFlight = null, restoreFlight = null;
  const listeners = new Set();
  const publish = value => { user = value; listeners.forEach(listener => listener(value)); };
  const expired = () => new ApiError('Сессия истекла. Войдите в клуб снова.', 401, 'UNAUTHORIZED');
  const serialize = operation => {
    const result = cookieQueue.then(() => locks ? locks.request('musical-monday:auth-cookie', operation) : operation());
    cookieQueue = result.catch(() => {});
    return result;
  };

  async function raw(path, { signal, body, headers: extraHeaders, cookie = false, access, ...options } = {}) {
    signal?.throwIfAborted();
    if (demo) {
      const { demoRequest } = await import('./demo.js');
      signal?.throwIfAborted();
      return demoRequest(path, options.method || 'GET');
    }
    const multipart = body instanceof FormData;
    const headers = new Headers(extraHeaders);
    if (body !== undefined && !multipart) headers.set('Content-Type', 'application/json');
    if (access) headers.set('Authorization', `Bearer ${access}`);
    if (cookie) headers.set('X-Requested-With', 'XMLHttpRequest');
    try {
      const response = await fetcher(`${base}/api${path}`, {
        ...options, headers, credentials: cookie ? 'include' : 'same-origin',
        signal: AbortSignal.any([AbortSignal.timeout(20000), ...(signal ? [signal] : [])]),
        ...(body !== undefined ? { body: multipart ? body : JSON.stringify(body) } : {}),
      });
      if (response.status === 204) return null;
      const text = await response.text();
      let data = null;
      if (text) {
        try { data = JSON.parse(text); }
        catch { throw new ApiError('Сервис вернул неожиданный ответ. Попробуйте позже.', response.status); }
      }
      if (!response.ok) throw responseError(data, response.status, path);
      return data; // The image-cover PATCH legitimately returns JSON null.
    } catch (error) {
      if (signal?.aborted) throw signal.reason;
      if (error instanceof ApiError) throw error;
      throw new ApiError('Не удалось связаться с клубом. Проверьте подключение и попробуйте ещё раз.', 0, 'NETWORK');
    }
  }

  async function acceptAuth(result, expected) {
    if (!result?.access_token) throw new ApiError('Не удалось прочитать ответ авторизации.');
    const verified = await raw('/auth/me', { access: result.access_token });
    if (expected !== generation) throw expired();
    token = result.access_token; publish(verified);
    return verified;
  }

  function refreshSession() {
    if (refreshFlight) return refreshFlight;
    const expected = generation;
    const flight = serialize(async () => {
      if (expected !== generation) throw expired();
      try { return await acceptAuth(await raw('/auth/refresh', { method: 'POST', cookie: true }), expected); }
      catch (error) {
        if (error.status === 401 && expected === generation) { token = null; publish(null); }
        throw error;
      }
    });
    refreshFlight = flight;
    flight.finally(() => { if (refreshFlight === flight) refreshFlight = null; }).catch(() => {});
    return flight;
  }

  async function request(path, { auth = false, ...options } = {}) {
    options.signal?.throwIfAborted();
    const expected = generation;
    let usedToken = token;
    if (auth && !usedToken) {
      if (!user) throw expired();
      await refreshSession();
      options.signal?.throwIfAborted(); usedToken = token;
    }
    try { return await raw(path, { ...options, access: auth ? usedToken : undefined }); }
    catch (error) {
      if (!auth || error.status !== 401 || expected !== generation) throw error;
      try {
        // A concurrent request may already have rotated the token.
        if (token === usedToken) await refreshSession();
        options.signal?.throwIfAborted();
        if (!token || expected !== generation) throw expired();
        return await raw(path, { ...options, access: token }); // At most one replay.
      } catch (retryError) {
        if (retryError.status === 401 && expected === generation) { token = null; publish(null); onExpired(); }
        throw retryError;
      }
    }
  }

  const key = id => encodeURIComponent(id);
  async function allPages(path, signal) {
    const items = [];
    for (let page = 1; ; page += 1) {
      const result = await request(`${path}?page=${page}&page_size=100`, { signal });
      if (!Array.isArray(result?.items)) throw new ApiError('Не удалось прочитать список.');
      items.push(...result.items);
      if (!result.items.length || items.length >= result.total) return items;
    }
  }

  return {
    request, getSession: () => user,
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    restoreSession() {
      if (!restoreFlight) {
        restoreFlight = demo ? Promise.resolve(null) : refreshSession().catch(error => { if (error.status === 401) return null; throw error; });
        restoreFlight.finally(() => { restoreFlight = null; }).catch(() => {});
      }
      return restoreFlight;
    },
    authenticate(mode, username, password) {
      const expected = ++generation;
      return serialize(async () => acceptAuth(await raw(`/auth/${mode}`, { method: 'POST', cookie: true, body: { username, password } }), expected));
    },
    login(username, password) { return this.authenticate('login', username, password); },
    register(username, password) { return this.authenticate('register', username, password); },
    async logout() {
      ++generation;
      await serialize(() => raw('/auth/logout', { method: 'POST', cookie: true }));
      token = null; publish(null);
    },
    concerts: signal => allPages('/afisha', signal),
    concert: (id, signal) => request(`/afisha/${key(id)}`, { signal }),
    venues: signal => allPages('/venues', signal),
    venue: (id, signal) => request(`/venues/${key(id)}`, { signal }),
    messages: (id, { signal, before, limit = 50 } = {}) => request(`/afisha/${key(id)}/messages?${new URLSearchParams({ limit, ...(before ? { before } : {}) })}`, { signal }),
    sendMessage: (id, text, signal) => request(`/afisha/${key(id)}/messages`, { method: 'POST', body: { text }, auth: true, signal }),
    async reviews(id, signal) {
      const items = [];
      for (let offset = 0; ; offset += 100) {
        const result = await request(`/afisha/${key(id)}/reviews?limit=100&offset=${offset}`, { signal });
        if (!Array.isArray(result?.items)) throw new ApiError('Не удалось прочитать отзывы.');
        items.push(...result.items);
        if (result.items.length < 100 || items.length >= result.stats.reviews_count) return { ...result, items };
      }
    },
    createReview: (id, body, signal) => request(`/afisha/${key(id)}/reviews`, { method: 'POST', body, auth: true, signal }),
    updateReview: (id, reviewId, body, signal) => request(`/afisha/${key(id)}/reviews/${key(reviewId)}`, { method: 'PATCH', body, auth: true, signal }),
    deleteReview: (id, reviewId, signal) => request(`/afisha/${key(id)}/reviews/${key(reviewId)}`, { method: 'DELETE', auth: true, signal }),
    createVenue: (body, signal) => request('/venues', { method: 'POST', body, auth: true, signal }),
    updateVenue: (id, body, signal) => request(`/venues/${key(id)}`, { method: 'PUT', body, auth: true, signal }),
    deleteVenue: (id, signal) => request(`/venues/${key(id)}`, { method: 'DELETE', auth: true, signal }),
    createConcert(body, images, signal) {
      const form = new FormData(); form.append('afisha', JSON.stringify(body));
      for (const image of images) form.append('images', image);
      return request('/afisha', { method: 'POST', body: form, auth: true, signal });
    },
    updateConcert: (id, body, signal) => request(`/afisha/${key(id)}`, { method: 'PUT', body, auth: true, signal }),
    deleteConcert: (id, signal) => request(`/afisha/${key(id)}`, { method: 'DELETE', auth: true, signal }),
    addImage(id, image, signal) {
      const form = new FormData(); form.append('image', image);
      return request(`/afisha/${key(id)}/images`, { method: 'POST', body: form, auth: true, signal });
    },
    coverImage: (id, imageId, signal) => request(`/afisha/${key(id)}/images/${key(imageId)}`, { method: 'PATCH', auth: true, signal }),
    deleteImage: (id, imageId, signal) => request(`/afisha/${key(id)}/images/${key(imageId)}`, { method: 'DELETE', auth: true, signal }),
  };
}

export const api = createApiClient();

export function mediaUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith('/') && !path.startsWith('//')) return `${BASE}${path}`;
  return '';
}

export function discussionSocketUrl(origin = globalThis.location?.href) {
  const url = new URL(`${BASE}/api/ws`, origin);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return url.href;
}

export function connectDiscussion(id, { onUpdate, onStatus, WebSocketImpl = globalThis.WebSocket, url = discussionSocketUrl(), schedule = setTimeout, cancel = clearTimeout } = {}) {
  if (DEMO) return () => {};
  let stopped = false, socket, retryTimer, pingTimer, watchdog, stableTimer, attempts = 0;
  const retryDelays = [1000, 2000, 4000, 8000, 15000];
  const clearConnectionTimers = () => { cancel(pingTimer); cancel(watchdog); cancel(stableTimer); };
  function connect() {
    if (stopped) return;
    onStatus?.('connecting');
    try { socket = new WebSocketImpl(url); } catch { retry(); return; }
    const current = socket;
    watchdog = schedule(() => current.close(), 15000);
    current.onopen = () => {
      if (stopped) { current.close(); return; }
      cancel(watchdog);
      current.send(JSON.stringify({ action: 'switch_afisha', afisha_id: id }));
      watchdog = schedule(() => current.close(), 15000);
    };
    const ping = () => {
      current.send(JSON.stringify({ action: 'ping' }));
      watchdog = schedule(() => current.close(), 10000);
    };
    current.onmessage = event => {
      if (stopped) return;
      let data;
      try { data = JSON.parse(event.data); } catch { return; }
      if (data.type === 'subscribed' && data.afisha_id === id) {
        cancel(watchdog); onStatus?.('connected'); onUpdate?.();
        stableTimer = schedule(() => { attempts = 0; }, 60000);
        pingTimer = schedule(ping, 25000);
      } else if (data.type === 'pong') {
        cancel(watchdog); pingTimer = schedule(ping, 25000);
      } else if (data.n_type === 2 || data.n_type === 3) onUpdate?.();
    };
    current.onerror = () => current.close();
    current.onclose = () => { clearConnectionTimers(); if (!stopped) retry(); };
  }
  function retry() {
    if (stopped) return;
    clearConnectionTimers(); onStatus?.(attempts < retryDelays.length ? 'reconnecting' : 'offline');
    if (attempts < retryDelays.length) retryTimer = schedule(connect, retryDelays[attempts++]);
  }
  connect();
  return () => {
    stopped = true; cancel(retryTimer); clearConnectionTimers();
    if (socket) { socket.onclose = socket.onmessage = socket.onopen = socket.onerror = null; socket.close(); }
  };
}
