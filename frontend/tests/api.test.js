import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiError, createApiClient, mediaUrl } from '../src/api.js';

const user = { id: 'user-1', username: 'listener', role: 'user' };
const json = (body, status = 200) => new Response(JSON.stringify(body), { status });
const auth = access_token => json({ ...user, access_token, expires_in: 60 });
const unauthorized = () => json({ detail: { error: { code: 'UNAUTHORIZED' } } }, 401);
function fixture(handler) {
  const calls = [];
  const client = createApiClient({ demo: false, locks: null, onExpired() {}, fetcher: async (url, options) => {
    const call = { path: url.replace('/api', ''), ...options }; calls.push(call);
    return handler(call, calls);
  } });
  return { client, calls };
}

test('plans load from the account and POST/DELETE use the authenticated follow endpoints', async () => {
  const { client, calls } = fixture(call => {
    if (call.path === '/auth/login') return auth('follow-token');
    if (call.path === '/auth/me') return json(user);
    if (call.path === '/auth/me/follows') return json(['concert-id']);
    return new Response(null, { status: 204 });
  });
  await client.login('listener', 'password123');
  assert.deepEqual(await client.followedConcerts(), ['concert-id']);
  await client.followConcert('concert-id');
  await client.unfollowConcert('concert-id');
  assert.deepEqual(calls.slice(2).map(call => [call.path, call.method || 'GET']), [
    ['/auth/me/follows', 'GET'], ['/afisha/concert-id/follow', 'POST'], ['/afisha/concert-id/follow', 'DELETE'],
  ]);
  for (const call of calls.slice(2)) assert.equal(call.headers.get('Authorization'), 'Bearer follow-token');
});

test('register immediately verifies and signs in; all cookie operations carry CSRF + credentials', async () => {
  const { client, calls } = fixture(call => {
    if (call.path === '/auth/me') return json(user);
    if (call.path === '/auth/logout') return new Response(null, { status: 204 });
    return auth('memory-only');
  });
  const sessions = []; client.subscribe(value => sessions.push(value));
  await client.register('listener', 'password123');
  assert.deepEqual(client.getSession(), user);
  assert.equal('access_token' in client.getSession(), false);
  assert.equal(calls[1].headers.get('Authorization'), 'Bearer memory-only');
  assert.deepEqual(JSON.parse(calls[0].body), { username: 'listener', password: 'password123' });
  await client.login('listener', 'password123');
  await client.restoreSession();
  await client.logout();
  assert.equal(client.getSession(), null);
  assert.equal(sessions.at(-1), null);
  for (const call of calls.filter(call => call.method === 'POST')) {
    assert.equal(call.credentials, 'include');
    assert.equal(call.headers.get('X-Requested-With'), 'XMLHttpRequest');
    assert.equal(call.headers.has('Authorization'), false);
  }
});

test('reload restores through refresh then /me, without a stored token', async () => {
  const { client, calls } = fixture(call => call.path === '/auth/refresh' ? auth('restored') : json(user));
  await Promise.all([client.restoreSession(), client.restoreSession()]);
  assert.deepEqual(calls.map(call => call.path), ['/auth/refresh', '/auth/me']);
  assert.deepEqual(client.getSession(), user);
});

test('missing refresh cookie is a normal guest session', async () => {
  const { client, calls } = fixture(() => unauthorized());
  assert.equal(await client.restoreSession(), null);
  assert.equal(client.getSession(), null);
  assert.equal(calls.length, 1);
});

test('simultaneous 401 responses share one refresh and replay each request once', async () => {
  let refreshes = 0;
  const { client, calls } = fixture(async call => {
    if (call.path === '/auth/login') return auth('old');
    if (call.path === '/auth/me') return json(user);
    if (call.path === '/auth/refresh') { refreshes++; await new Promise(resolve => setTimeout(resolve, 10)); return auth('new'); }
    return call.headers.get('Authorization') === 'Bearer old' ? unauthorized() : json({ id: call.path });
  });
  await client.login('listener', 'password123');
  await Promise.all([client.sendMessage('concert', 'one'), client.createReview('concert', { rating: 5, text: 'two' })]);
  assert.equal(refreshes, 1);
  for (const path of ['/afisha/concert/messages', '/afisha/concert/reviews']) {
    const writes = calls.filter(call => call.path === path);
    assert.equal(writes.length, 2); assert.equal(writes[1].body, writes[0].body);
  }
});

test('a late 401 uses an already rotated token without another refresh', async () => {
  let releaseLate;
  const late = new Promise(resolve => { releaseLate = resolve; });
  let freshUsed; const used = new Promise(resolve => { freshUsed = resolve; });
  let refreshes = 0;
  const { client } = fixture(async call => {
    if (call.path === '/auth/login') return auth('old');
    if (call.path === '/auth/me') return json(user);
    if (call.path === '/auth/refresh') { refreshes++; return auth('new'); }
    if (call.headers.get('Authorization') === 'Bearer old') {
      if (call.path === '/late') await late;
      return unauthorized();
    }
    freshUsed(); return json({ ok: true });
  });
  await client.login('listener', 'password123');
  const first = client.request('/first', { auth: true });
  const second = client.request('/late', { auth: true });
  await used; releaseLate(); await Promise.all([first, second]);
  assert.equal(refreshes, 1);
});

test('a replayed 401 expires the session with no retry loop', async () => {
  let expired = 0;
  const calls = [];
  const client = createApiClient({ demo: false, locks: null, onExpired: () => expired++, fetcher: async (url, options) => {
    calls.push(url);
    if (url.endsWith('/auth/me')) return json(user);
    if (url.includes('/auth/')) return auth('token');
    return unauthorized();
  } });
  await client.login('listener', 'password123');
  await assert.rejects(client.sendMessage('c', 'hello'), error => error.status === 401);
  assert.equal(calls.filter(path => path.endsWith('/auth/refresh')).length, 1);
  assert.equal(calls.filter(path => path.endsWith('/messages')).length, 2);
  assert.equal(expired, 1); assert.equal(client.getSession(), null);
});

test('forbidden action preserves session and never refreshes', async () => {
  const { client, calls } = fixture(call => {
    if (call.path === '/auth/me') return json(user);
    if (call.path === '/auth/login') return auth('token');
    return json({ detail: { error: { code: 'FORBIDDEN' } } }, 403);
  });
  await client.login('listener', 'password123');
  await assert.rejects(client.createVenue({ name: 'room' }), error => error.status === 403 && /нет прав/.test(error.message));
  assert.deepEqual(client.getSession(), user);
  assert.equal(calls.some(call => call.path === '/auth/refresh'), false);
});

test('wrong password, expired session, conflicts, validation and network errors are distinct', async () => {
  for (const [path, status, body, expected] of [
    ['/auth/login', 401, {}, /Неверное имя/],
    ['/auth/refresh', 401, {}, /Сессия истекла/],
    ['/auth/register', 409, { detail: { error: { code: 'USERNAME_ALREADY_EXISTS' } } }, /имя уже занято/],
    ['/afisha/c/reviews', 409, { detail: { error: { code: 'review_already_exists' } } }, /уже оставили отзыв/],
    ['/venues', 409, {}, /Данные уже изменились/],
    ['/venues', 422, { detail: [] }, /Проверьте обязательные/],
    ['/auth/login', 403, { detail: { error: { code: 'CSRF_FAILED' } } }, /источник запроса/],
  ]) {
    const { client } = fixture(() => json(body, status));
    await assert.rejects(client.request(path), error => error.status === status && expected.test(error.message));
  }
  const { client } = fixture(() => { throw new TypeError('Failed to fetch'); });
  await assert.rejects(client.request('/afisha'), error => error instanceof ApiError && error.code === 'NETWORK' && error.status === 0);
});

test('204 deletes and the JSON-null cover response need no JSON object', async () => {
  const { client } = fixture(call => call.path === '/auth/login' ? auth('token') : call.path === '/auth/me' ? json(user) : call.method === 'PATCH' ? json(null) : new Response(null, { status: 204 }));
  await client.login('listener', 'password123');
  assert.equal(await client.deleteReview('c', 'r'), null);
  assert.equal(await client.deleteConcert('c'), null);
  assert.equal(await client.deleteVenue('v'), null);
  assert.equal(await client.deleteImage('c', 'i'), null);
  assert.equal(await client.coverImage('c', 'i'), null);
});

test('multipart uses exact backend fields and lets the browser set its boundary; updates use JSON', async () => {
  const { client, calls } = fixture(call => call.path === '/auth/login' ? auth('token') : call.path === '/auth/me' ? json(user) : json({ id: 'saved' }));
  await client.login('listener', 'password123');
  const image = new File(['image bytes'], 'poster.png', { type: 'image/png' });
  const body = { title: 'Concert', venue_ids: ['v'] };
  await client.createConcert(body, [image]); await client.addImage('c', image);
  await client.updateConcert('c', body); await client.updateVenue('v', { name: 'Hall' });
  const create = calls.find(call => call.path === '/afisha');
  assert.deepEqual(JSON.parse(create.body.get('afisha')), body);
  assert.equal(create.body.getAll('images').length, 1);
  assert.equal(create.headers.has('Content-Type'), false);
  const add = calls.find(call => call.path.endsWith('/images'));
  assert.equal(add.body.get('image').name, 'poster.png'); assert.equal(add.headers.has('Content-Type'), false);
  for (const call of calls.filter(call => call.method === 'PUT')) assert.equal(call.headers.get('Content-Type'), 'application/json');
});

test('cancellation is preserved and does not become a network error', async () => {
  const controller = new AbortController();
  const { client, calls } = fixture(() => json({}));
  controller.abort();
  await assert.rejects(client.concert('c', controller.signal), { name: 'AbortError' });
  assert.equal(calls.length, 0);
  const inFlight = fixture(call => new Promise((resolve, reject) => call.signal.addEventListener('abort', () => reject(call.signal.reason))));
  const second = new AbortController(); const request = inFlight.client.concert('c', second.signal);
  second.abort(); await assert.rejects(request, { name: 'AbortError' });
});

test('canceling one waiter never cancels the shared refresh', async () => {
  let finish; const wait = new Promise(resolve => { finish = resolve; });
  const { client } = fixture(async call => {
    if (call.path === '/auth/login') return auth('old');
    if (call.path === '/auth/me') return json(user);
    if (call.path === '/auth/refresh') { await wait; return auth('new'); }
    return call.headers.get('Authorization') === 'Bearer old' ? unauthorized() : json({ ok: true });
  });
  await client.login('listener', 'password123');
  const controller = new AbortController();
  const one = client.request('/one', { auth: true, signal: controller.signal });
  const two = client.request('/two', { auth: true });
  await new Promise(resolve => setTimeout(resolve, 0)); controller.abort(); finish();
  await assert.rejects(one, { name: 'AbortError' });
  assert.deepEqual(await two, { ok: true }); assert.deepEqual(client.getSession(), user);
});

test('logout queues behind refresh and a stale refresh cannot restore a logged-out user', async () => {
  let finish; const wait = new Promise(resolve => { finish = resolve; });
  const { client, calls } = fixture(async call => {
    if (call.path === '/auth/refresh') { await wait; return auth('new'); }
    if (call.path === '/auth/logout') return new Response(null, { status: 204 });
    return json(user);
  });
  const restoring = client.restoreSession();
  await new Promise(resolve => setTimeout(resolve, 0));
  const logout = client.logout(); finish(); await Promise.all([restoring, logout]);
  assert.equal(client.getSession(), null);
  assert.ok(calls.findIndex(call => call.path === '/auth/logout') > calls.findIndex(call => call.path === '/auth/refresh'));
});

test('lists paginate; message cursor is opaque and encoded; reviews include older own reviews', async () => {
  const { client, calls } = fixture(call => {
    const url = new URL(call.path, 'http://test');
    if (url.pathname.endsWith('/messages')) return json({ items: [], next_cursor: null, has_more: false });
    if (url.pathname.endsWith('/reviews')) {
      const offset = Number(url.searchParams.get('offset'));
      return json({ stats: { reviews_count: 101, rating_sum: 505 }, items: offset ? [{ id: 'own', author_id: user.id }] : Array.from({ length: 100 }, (_, id) => ({ id })) });
    }
    return json({ items: [{ id: url.searchParams.get('page') }], total: 2 });
  });
  assert.equal((await client.concerts()).length, 2); assert.equal((await client.venues()).length, 2);
  await client.messages('c', { before: 'opaque+/=cursor' });
  assert.equal(new URL(calls.at(-1).path, 'http://test').searchParams.get('before'), 'opaque+/=cursor');
  assert.equal((await client.reviews('c')).items.at(-1).id, 'own');
  assert.equal(mediaUrl('/uploads/poster.png'), '/uploads/poster.png');
  assert.equal(mediaUrl('//other-site/poster.png'), ''); assert.equal(mediaUrl('javascript:bad'), '');
});
