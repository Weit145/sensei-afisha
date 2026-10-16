import { Component, useEffect, useId, useRef, useState } from 'react';
import { api, MAP_ATTRIBUTION, MAP_TILE_URL } from './api.js';
import { Icon } from './components.jsx';
import { coordinates, osmLink, roundedCoordinates } from './mapUtils.js';
import 'leaflet/dist/leaflet.css';

class MapBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    return this.state.failed ? <div className="map-error" role="alert"><p>Не удалось открыть карту. {this.props.editable ? 'Адрес и координаты можно указать вручную.' : 'Адрес площадки указан выше.'}</p><button type="button" className="inline-button" onClick={() => this.setState({ failed: false })}>Открыть карту заново</button></div> : this.props.children;
  }
}

export default function VenueMap(props) { return <MapBoundary editable={Boolean(props.onChange)}><VenueMapContent {...props} /></MapBoundary>; }

function VenueMapContent({ latitude, longitude, onChange, name = 'Площадка', query = '', disabled = false }) {
  const editable = Boolean(onChange), point = coordinates(latitude, longitude);
  const [loading, setLoading] = useState(true), [error, setError] = useState(''), [revision, setRevision] = useState(0);
  const [searching, setSearching] = useState(false), [searchError, setSearchError] = useState(''), [results, setResults] = useState(null), [status, setStatus] = useState('');
  const elementRef = useRef(null), mapRef = useRef(null), markerRef = useRef(null), layerRef = useRef(null), searchController = useRef(null);
  const valuesRef = useRef({ point, onChange, disabled }); valuesRef.current = { point, onChange, disabled };
  const hintId = useId();
  const fallbackText = editable ? 'Адрес и координаты можно указать вручную.' : 'Адрес площадки указан выше.';

  useEffect(() => {
    const controller = new AbortController();
    let map, timer, resizeObserver;
    setLoading(true); setError('');
    async function mount() {
      try {
        if (!MAP_TILE_URL) throw new Error(`Карта отключена. ${fallbackText}`);
        const imported = await import('leaflet'); const L = imported.default || imported;
        if (controller.signal.aborted) return;
        map = L.map(elementRef.current, { scrollWheelZoom: false, keyboard: true, zoomControl: true, maxZoom: 19 }); mapRef.current = map;
        const current = valuesRef.current.point;
        map.setView(current || [20, 0], current ? 16 : 2);
        map.getContainer().setAttribute('aria-label', editable ? 'Карта выбора положения площадки' : `Расположение: ${name}`);
        map.getContainer().setAttribute('aria-describedby', hintId);
        map.getContainer().setAttribute('role', 'region');
        const credit = document.createElement('a'); credit.href = 'https://www.openstreetmap.org/copyright'; credit.target = '_blank'; credit.rel = 'noopener noreferrer'; credit.textContent = MAP_ATTRIBUTION;
        const layer = L.tileLayer(MAP_TILE_URL, { attribution: credit.outerHTML, maxZoom: 19, updateWhenIdle: true, keepBuffer: 1 }); layerRef.current = layer;
        let tilesStarted = 0, tilesFailed = 0, tilesLoaded = 0;
        const ready = () => { clearTimeout(timer); setLoading(false); };
        layer.on('tileloadstart', () => { tilesStarted++; });
        layer.on('tileload', () => { tilesLoaded++; if (!controller.signal.aborted) { ready(); setError(''); } });
        layer.on('tileerror', () => { tilesFailed++; if (!controller.signal.aborted && !tilesLoaded && tilesFailed >= tilesStarted) { ready(); setError(`Не удалось загрузить карту. ${fallbackText}`); } });
        layer.addTo(map);
        timer = setTimeout(() => { if (!controller.signal.aborted && !tilesLoaded) { setLoading(false); setError(`Карта не отвечает. ${fallbackText}`); } }, 12000);
        const setPoint = location => {
          if (valuesRef.current.disabled || !tilesLoaded) return;
          const value = roundedCoordinates({ lat: Math.max(-90, Math.min(90, location.lat)), lng: ((location.lng + 180) % 360 + 360) % 360 - 180 });
          valuesRef.current.onChange?.(value); setStatus(`Маркер установлен: ${value.latitude}, ${value.longitude}. Сохраните площадку, чтобы записать положение.`);
        };
        const marker = L.marker(current || [0, 0], {
          draggable: editable, keyboard: true, title: 'Положение площадки', alt: 'Положение площадки',
          icon: L.divIcon({ className: 'venue-map-marker', html: '<span aria-hidden="true"></span>', iconSize: [30, 38], iconAnchor: [15, 37] }),
        });
        markerRef.current = marker;
        if (current) marker.addTo(map); // A default viewport never creates a fictitious marker.
        if (editable) {
          marker.on('dragend', () => setPoint(marker.getLatLng()));
          map.on('click', event => setPoint(event.latlng));
          map.getContainer().addEventListener('keydown', event => {
            if (event.target === map.getContainer() && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault(); setPoint(map.getCenter()); }
          }, { signal: controller.signal });
        }
        resizeObserver = new ResizeObserver(() => map.invalidateSize({ pan: false })); resizeObserver.observe(elementRef.current);
        map.invalidateSize({ pan: false });
      } catch (error) { if (!controller.signal.aborted) { setLoading(false); setError(error.message || `Не удалось открыть карту. ${fallbackText}`); } }
    }
    mount();
    return () => { controller.abort(); clearTimeout(timer); resizeObserver?.disconnect(); map?.remove(); mapRef.current = markerRef.current = layerRef.current = null; };
  }, [editable, hintId, name, revision]);

  useEffect(() => {
    const map = mapRef.current, marker = markerRef.current;
    if (!map || !marker) return;
    if (point) {
      marker.setLatLng(point);
      if (!map.hasLayer(marker)) marker.addTo(map);
      if (!map.getBounds().contains(point) || map.getZoom() < 12) map.setView(point, 16, { animate: false });
    } else if (map.hasLayer(marker)) marker.remove();
    if (editable) { if (disabled) marker.dragging?.disable(); else marker.dragging?.enable(); }
  }, [latitude, longitude, editable, disabled, loading]);
  useEffect(() => () => searchController.current?.abort(), []);
  useEffect(() => { searchController.current?.abort(); setSearching(false); setResults(null); setSearchError(''); }, [query]);

  async function search() {
    searchController.current?.abort();
    const controller = new AbortController(); searchController.current = controller;
    setSearching(true); setSearchError(''); setResults(null);
    try { const items = await api.searchPlaces(query, controller.signal); if (!controller.signal.aborted) setResults(items); }
    catch (error) { if (!controller.signal.aborted) setSearchError(error.message); }
    finally { if (!controller.signal.aborted) setSearching(false); }
  }

  return <section className={`venue-map-section ${editable ? 'map-picker' : ''}`} aria-label={editable ? 'Выбор площадки на карте' : `Карта: ${name}`}>
    {editable && <div className="map-search"><button type="button" className="button secondary" onClick={search} disabled={disabled || searching || query.trim().length < 3}>{searching ? 'Ищем площадку…' : 'Найти по адресу'}<Icon name="search" size={16} /></button><p className="small-text muted">Поиск по указанным городу и адресу. Выберите подходящий результат — название и адрес останутся введёнными вами.</p></div>}
    {searchError && <p className="form-error" role="alert">{searchError}</p>}
    {results && <div className="map-search-results" aria-live="polite">{!results.length ? <p>Адрес не найден. Уточните его или выберите точку на карте.</p> : <ul>{results.map((result, index) => <li key={`${result.latitude}:${result.longitude}:${index}`}><button type="button" disabled={disabled} onClick={() => { onChange({ latitude: result.latitude, longitude: result.longitude }); setResults(null); setStatus('Положение выбрано из результата поиска. Проверьте точку и сохраните площадку.'); }}>{result.label}<span>{result.latitude.toFixed(6)}, {result.longitude.toFixed(6)}</span></button></li>)}</ul>}<small>Поиск: Photon · данные OpenStreetMap</small></div>}
    <div className="venue-map-frame"><div ref={elementRef} className="venue-map" />{loading && <div className="map-loading" role="status">Загружаем карту…</div>}</div>
    {error && <div className="map-error" role="alert"><p>{error}</p><button type="button" className="inline-button" disabled={disabled} onClick={() => setRevision(value => value + 1)}>Повторить загрузку карты</button></div>}
    <p className="map-hint" id={hintId}>{editable ? 'Кликните по карте или перетащите маркер. С клавиатуры: стрелки сдвигают карту, + и − меняют масштаб, Enter ставит маркер в центре. Координаты также можно ввести вручную.' : 'Карту можно перемещать стрелками; + и − меняют масштаб.'}</p>
    {editable && !point && <p className="map-hint">Положение ещё не выбрано. Обзор карты не является координатами площадки.</p>}
    {point && <div className="map-position"><span>{point[0].toFixed(6)}, {point[1].toFixed(6)}</span><a className="inline-button" target="_blank" rel="noopener noreferrer" href={osmLink(point)}>Открыть карту<Icon name="external" size={14} /></a>{editable && <button type="button" className="inline-button" disabled={disabled} onClick={() => { onChange({ latitude: '', longitude: '' }); setStatus('Маркер убран. Сохраните площадку, чтобы удалить координаты.'); }}>Убрать маркер</button>}</div>}
    {editable && <p className="map-status" role="status">{status}</p>}
  </section>;
}
