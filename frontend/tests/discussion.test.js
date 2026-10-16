import test from 'node:test';
import assert from 'node:assert/strict';
import { connectDiscussion, discussionSocketUrl } from '../src/api.js';
import { averageRating, canCreateReview, mergeMessages } from '../src/utils.js';

function socketFixture() {
  const sockets = [], timers = new Map(); let next = 0;
  class Socket {
    constructor(url) { this.url = url; this.sent = []; sockets.push(this); }
    send(data) { this.sent.push(JSON.parse(data)); }
    close() { this.closed = true; this.onclose?.(); }
    message(data) { this.onmessage?.({ data: JSON.stringify(data) }); }
  }
  let updates = 0; const statuses = [], participants = [];
  const stop = connectDiscussion('concert-id', { url: 'ws://test/api/ws', WebSocketImpl: Socket, onUpdate: () => updates++, onParticipant: value => participants.push(value), onStatus: value => statuses.push(value), schedule: (fn, delay) => { const id = ++next; timers.set(id, { fn, delay }); return id; }, cancel: id => timers.delete(id) });
  const tick = delay => { const entry = [...timers].find(([, value]) => value.delay === delay); assert.ok(entry, `timer ${delay} exists`); timers.delete(entry[0]); entry[1].fn(); };
  return { sockets, timers, tick, stop, statuses, participants, get updates() { return updates; } };
}

test('socket subscribes, invalidates GET history, pings, and cleans up on leave', () => {
  const f = socketFixture(), socket = f.sockets[0];
  socket.onopen(); assert.deepEqual(socket.sent[0], { action: 'switch_afisha', afisha_id: 'concert-id' });
  socket.message({ type: 'connected' }); assert.equal(f.updates, 0);
  socket.message({ type: 'subscribed', afisha_id: 'concert-id' }); assert.equal(f.updates, 1);
  socket.message({ n_type: 2, text: 'Notification text is never a message', user_id: 'u' }); assert.equal(f.updates, 2);
  socket.message({ n_type: 3 }); assert.equal(f.updates, 3);
  socket.message({ n_type: 2, user_id: 'author', nickname: 'true_nickname', text: 'not a persisted message' });
  assert.deepEqual(f.participants, [{ user_id: 'author', nickname: 'true_nickname' }]); assert.equal(f.updates, 4);
  f.tick(25000); assert.deepEqual(socket.sent.at(-1), { action: 'ping' });
  socket.message({ type: 'pong' }); assert.equal([...f.timers.values()].some(value => value.delay === 10000), false);
  f.stop(); assert.equal(socket.closed, true); assert.equal(f.timers.size, 0); assert.equal(socket.onmessage, null);
});

test('socket retries are bounded even when a server repeatedly connects then closes', () => {
  const f = socketFixture();
  for (const delay of [1000, 2000, 4000, 8000, 15000]) {
    const socket = f.sockets.at(-1); socket.onopen(); socket.message({ type: 'subscribed', afisha_id: 'concert-id' }); socket.close(); f.tick(delay);
  }
  f.sockets.at(-1).close();
  assert.equal(f.sockets.length, 6); assert.equal(f.statuses.at(-1), 'offline'); assert.equal(f.timers.size, 0); f.stop();
});

test('missing pong closes a stale connection and reconnects', () => {
  const f = socketFixture(), socket = f.sockets[0];
  socket.onopen(); socket.message({ type: 'subscribed', afisha_id: 'concert-id' });
  f.tick(25000); f.tick(10000); assert.equal(socket.closed, true); f.tick(1000); assert.equal(f.sockets.length, 2); f.stop();
  assert.equal(discussionSocketUrl('https://club.example/concert/c'), 'wss://club.example/api/ws');
});

test('history merges by id with deterministic order and never duplicates a sent message', () => {
  const a = { id: 'a', created_at: '2026-10-01T10:00:00Z', text: 'first' }, b = { id: 'b', created_at: a.created_at, text: 'second' };
  assert.deepEqual(mergeMessages([b], [a, b, { ...b, text: 'from GET' }]).map(item => [item.id, item.text]), [['a', 'first'], ['b', 'from GET']]);
});

test('ratings use sum/count and review creation requires a finished published concert', () => {
  assert.equal(averageRating({ rating_sum: 9, reviews_count: 2 }), '4.5'); assert.equal(averageRating({ rating_sum: 0, reviews_count: 0 }), null);
  const now = Date.parse('2026-10-17T10:00:00Z');
  assert.equal(canCreateReview({ status: 'published', ends_at: '2026-10-17T09:59:00Z' }, now), true);
  assert.equal(canCreateReview({ status: 'published', ends_at: '2026-10-17T10:01:00Z' }, now), false);
  assert.equal(canCreateReview({ status: 'cancelled', ends_at: '2026-10-17T09:59:00Z' }, now), false);
});
