export function coordinates(latitude, longitude) {
  if ([latitude, longitude].some(value => value == null || typeof value === 'boolean' || (typeof value === 'string' && !value.trim()))) return null;
  const lat = Number(latitude), lng = Number(longitude);
  return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180 ? [lat, lng] : null;
}

export const roundedCoordinates = point => ({ latitude: Number(point.lat.toFixed(6)), longitude: Number(point.lng.toFixed(6)) });
export const osmLink = point => `https://www.openstreetmap.org/?mlat=${point[0]}&mlon=${point[1]}#map=16/${point[0]}/${point[1]}`;
