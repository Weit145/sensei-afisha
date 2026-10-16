import test from 'node:test';
import assert from 'node:assert/strict';
import { createApiClient } from '../src/api.js';
import { contactValue, contactsPayload } from '../src/contactsUtils.js';

const user = { id: 'user', username: 'listener', role: 'user' };
const response = (data, status = 200) => new Response(JSON.stringify(data), { status });
function clientFixture(handler) {
  const calls = [], notifications = [];
  const client = createApiClient({ demo: false, locks: null, onExpired: () => notifications.push('expired'), fetcher: async (url, options) => {
    const call = { url, ...options }; calls.push(call);
    if (url.endsWith('/auth/login')) return response({ ...user, access_token: 'old' });
    if (url.endsWith('/auth/me')) return response(user);
    return handler(call);
  } });
  return { client, calls, notifications };
}

test('contact URLs match backend domains; empty input deletes a contact', () => {
  for (const value of ['https://t.me/listener', 'https://telegram.me/listener', ' https://T.ME/listener ']) assert.equal(contactValue(value, 'tg_url'), value.trim());
  assert.equal(contactValue('https://vk.com/listener', 'vk_url'), 'https://vk.com/listener');
  assert.deepEqual(contactsPayload({ tg_url: ' ', vk_url: '' }), { body: { tg_url: null, vk_url: null }, errors: {} });
  for (const value of ['http://t.me/listener', 'https://t.me/', 'https://t.me:443/listener', 'https://user@t.me/listener', 'https://t.me.evil.test/listener', 'https://vk.com/listener', 'javascript:alert(1)', 'https://t.me/hello world', 'https://t.me\\evil.test/name', `https://t.me/${'a'.repeat(256)}`]) assert.throws(() => contactValue(value, 'tg_url'), value);
  assert.throws(() => contactValue('https://telegram.me/listener', 'vk_url'));
  const invalid = contactsPayload({ tg_url: 'bad', vk_url: 'bad' });
  assert.deepEqual(Object.keys(invalid.errors), ['tg_url', 'vk_url']);
});

test('own contacts round-trip add/change/delete; PATCH includes CSRF and preserves omitted fields', async () => {
  let saved = { tg_url: null, vk_url: null };
  const { client, calls } = clientFixture(call => {
    if (call.method === 'PATCH') saved = { ...saved, ...JSON.parse(call.body) };
    return response(saved);
  });
  await client.login('listener', 'password');
  assert.deepEqual(await client.myContacts(), { tg_url: null, vk_url: null });
  await client.updateContacts({ tg_url: 'https://t.me/first', vk_url: 'https://vk.com/first' });
  await client.updateContacts({ tg_url: 'https://telegram.me/second' });
  assert.equal((await client.myContacts()).vk_url, 'https://vk.com/first');
  await client.updateContacts({ tg_url: null, vk_url: null });
  assert.deepEqual(await client.myContacts(), { tg_url: null, vk_url: null });
  for (const call of calls.filter(call => call.url.endsWith('/contacts'))) {
    assert.equal(call.headers.get('Authorization'), 'Bearer old'); assert.equal(call.cache, 'no-store');
    if (call.method === 'PATCH') { assert.equal(call.headers.get('X-Requested-With'), 'XMLHttpRequest'); assert.equal(call.headers.get('Content-Type'), 'application/json'); }
  }
  assert.deepEqual(JSON.parse(calls.filter(call => call.method === 'PATCH')[1].body), { tg_url: 'https://telegram.me/second' });
});

test('participant contacts use the author id and true nickname; missing contacts remain null', async () => {
  const data = { user_id: 'author-id', nickname: 'true_nickname', tg_url: null, vk_url: null };
  const { client, calls } = clientFixture(() => response(data)); await client.login('listener', 'password');
  assert.deepEqual(await client.userContacts('author-id'), data);
  assert.equal(calls.at(-1).url, '/api/users/author-id/contacts');
  assert.equal(calls.at(-1).headers.get('Authorization'), 'Bearer old');
});

test('deleted participant 404 can be retried without expiring the viewer session', async () => {
  let attempts = 0;
  const { client } = clientFixture(() => { attempts++; return response({ detail: { error: { code: 'not_found', message: 'Пользователь не найден' } } }, 404); });
  await client.login('listener', 'password');
  for (let i = 0; i < 2; i++) await assert.rejects(client.userContacts('deleted'), error => error.status === 404);
  assert.equal(attempts, 2); assert.deepEqual(client.getSession(), user);
});

test('expired contacts request refreshes once, then succeeds with new bearer', async () => {
  const { client, calls } = clientFixture(call => {
    if (call.url.endsWith('/auth/refresh')) return response({ access_token: 'new' });
    return call.headers.get('Authorization') === 'Bearer old' ? response({}, 401) : response({ tg_url: null, vk_url: null });
  });
  await client.login('listener', 'password'); await client.updateContacts({ tg_url: null });
  assert.equal(calls.filter(call => call.url.endsWith('/auth/refresh')).length, 1);
  const patches = calls.filter(call => call.method === 'PATCH');
  assert.equal(patches.length, 2); assert.equal(patches[1].headers.get('Authorization'), 'Bearer new');
  assert.equal(patches[1].headers.get('X-Requested-With'), 'XMLHttpRequest'); assert.equal(patches[1].body, patches[0].body);
});

test('expired refresh hides contacts by clearing session; validation errors identify the field', async () => {
  const expired = clientFixture(() => response({}, 401)); await expired.client.login('listener', 'password');
  await assert.rejects(expired.client.userContacts('author'), error => error.status === 401);
  assert.equal(expired.client.getSession(), null); assert.deepEqual(expired.notifications, ['expired']);
  const invalid = clientFixture(() => response({ detail: [{ loc: ['body', 'tg_url'], msg: 'invalid link' }] }, 422));
  await invalid.client.login('listener', 'password');
  await assert.rejects(invalid.client.updateContacts({ tg_url: 'bad' }), error => error.status === 422 && error.fields.tg_url.includes('HTTPS'));
});

test('guest never fetches participant contacts and canceled reads preserve AbortError', async () => {
  const { client, calls } = clientFixture(() => response({}));
  await assert.rejects(client.userContacts('author'), error => error.status === 401); assert.equal(calls.length, 0);
  await client.login('listener', 'password'); const controller = new AbortController(); controller.abort();
  await assert.rejects(client.myContacts(controller.signal), { name: 'AbortError' }); assert.equal(calls.length, 2);
});
