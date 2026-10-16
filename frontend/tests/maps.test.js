import test from 'node:test';
import assert from 'node:assert/strict';
import { createPlaceSearch } from '../src/api.js';
import { coordinates, osmLink, roundedCoordinates } from '../src/mapUtils.js';
import { venuePayload } from '../src/adminUtils.js';

const feature = { type: 'Feature', geometry: { type: 'Point', coordinates: [37.605, 55.756] }, properties: { name: 'Зал', city: 'Москва', street: 'Улица', housenumber: '1' } };
test('no marker exists for absent, partial or invalid coordinates; zero is a real coordinate', () => {
  for (const pair of [[null, null], ['', ''], [' ', ' '], [55, null], [undefined, 37], [91, 37], [55, 181], ['bad', 37], [false, false]]) assert.equal(coordinates(...pair), null);
  assert.deepEqual(coordinates(0, 0), [0, 0]); assert.deepEqual(coordinates('55.756', '37.605'), [55.756, 37.605]);
  assert.deepEqual(roundedCoordinates({ lat: 55.75612345, lng: 37.60512345 }), { latitude: 55.756123, longitude: 37.605123 });
  assert.match(osmLink([55.756, 37.605]), /mlat=55.756&mlon=37.605/);
});
test('geocoder uses external Photon protocol, no bearer/cookies, and cached results', async () => {
  const calls = [];
  const search = createPlaceSearch({ endpoint: 'https://geocoder.example/api/', fetcher: async (url, options) => { calls.push({ url, options }); return Response.json({ features: [feature] }); } });
  const result = await search('Москва, Улица 1'); assert.equal(result[0].latitude, 55.756); assert.equal(result[0].longitude, 37.605);
  assert.equal(result[0].label, 'Зал, Улица 1, Москва');
  result[0].latitude = 0; assert.equal((await search('Москва, Улица 1'))[0].latitude, 55.756);
  assert.equal(calls.length, 1); assert.equal(calls[0].options.credentials, 'omit'); assert.equal(calls[0].options.headers, undefined);
  const url = new URL(calls[0].url); assert.equal(url.searchParams.get('q'), 'Москва, Улица 1'); assert.equal(url.searchParams.get('limit'), '5');
});
test('search never fabricates a coordinate or accepts out-of-range results', async () => {
  const search = createPlaceSearch({ endpoint: 'https://geocoder.example/', fetcher: async () => Response.json({ features: [{ ...feature, geometry: { type: 'Point', coordinates: [0, 91] } }, { ...feature, geometry: { type: 'Point', coordinates: [0, null] } }] }) });
  assert.deepEqual(await search('Москва'), []);
});
test('disabled, failed and malformed geocoders fail clearly; manual venue save remains independent', async () => {
  await assert.rejects(createPlaceSearch({ endpoint: '' })('Москва'), /отключён/);
  for (const fetcher of [async () => { throw new TypeError('offline'); }, async () => new Response('', { status: 503 }), async () => Response.json({ wrong: [] })]) await assert.rejects(createPlaceSearch({ endpoint: 'https://geocoder.example/', fetcher })('Москва'), /вручную/);
  assert.deepEqual(venuePayload({ name: 'Зал', city: 'Москва', address: 'Адрес', latitude: '', longitude: '' }), { name: 'Зал', city: 'Москва', address: 'Адрес', latitude: null, longitude: null });
});
test('uncached searches are throttled; aborted queries never become fake empty results', async () => {
  let clock = 0;
  const search = createPlaceSearch({ endpoint: 'https://geocoder.example/', now: () => clock, fetcher: async () => Response.json({ features: [] }) });
  assert.deepEqual(await search('Москва'), []); await assert.rejects(search('Казань'), /Подождите/);
  clock = 1200; assert.deepEqual(await search('Казань'), []);
  const controller = new AbortController(); controller.abort(); await assert.rejects(search('Москва', controller.signal), { name: 'AbortError' });
});
