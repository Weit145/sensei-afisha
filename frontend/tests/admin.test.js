import test from 'node:test';
import assert from 'node:assert/strict';
import { concertPayload, moscowInput, validateImages, venuePayload } from '../src/adminUtils.js';

const valid = { title: ' Concert ', short_description: '', description: ' Program ', starts_at: '2026-10-19T19:00', ends_at: '2026-10-19T20:30', venue_ids: ['venue'], age_limit: '6', status: 'published' };
test('concert dates use Moscow even on a machine in another timezone', () => {
  const payload = concertPayload(valid);
  assert.equal(payload.starts_at, '2026-10-19T16:00:00.000Z'); assert.equal(payload.title, 'Concert');
  assert.equal(payload.age_limit, 6); assert.equal(payload.short_description, null);
  assert.equal(moscowInput(payload.starts_at), valid.starts_at);
});
test('invalid venue, dates, status and age are rejected before sending', () => {
  for (const invalid of [{ venue_ids: [] }, { starts_at: '' }, { ends_at: valid.starts_at }, { ends_at: '2026-10-19T18:00' }, { age_limit: '7' }, { status: 'draft' }, { title: '   ' }]) assert.throws(() => concertPayload({ ...valid, ...invalid }));
});
test('venues require address and reject invalid coordinates', () => {
  const venue = { name: ' Hall ', city: 'Moscow', address: 'Street', latitude: '', longitude: '' };
  assert.deepEqual(venuePayload(venue), { name: 'Hall', city: 'Moscow', address: 'Street', latitude: null, longitude: null });
  for (const invalid of [{ city: '' }, { address: '  ' }, { latitude: '91' }, { longitude: '-181' }, { latitude: 'NaN' }]) assert.throws(() => venuePayload({ ...venue, ...invalid }));
});
test('image signatures accept backend formats and reject disguised SVG', async () => {
  for (const bytes of [[255, 216, 255], [137, 80, 78, 71, 13, 10, 26, 10], new TextEncoder().encode('GIF89a'), new TextEncoder().encode('RIFF1234WEBP')]) await validateImages([new File([new Uint8Array(bytes)], 'poster')]);
  await assert.rejects(validateImages([new File(['<svg/>'], 'fake.png', { type: 'image/png' })]), /JPEG, PNG, GIF и WebP/);
});
