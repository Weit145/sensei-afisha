import { useEffect, useMemo, useState } from 'react';
import { api } from '../api.js';
import { DateLine, ErrorState, Icon, Link, Poster } from '../components.jsx';
import { averageRating, dateShort, filterConcerts, isPast, monthKey, monthLabel } from '../utils.js';

function HeroArt() {
  return <div className="hero-art" aria-hidden="true"><svg viewBox="0 0 540 430" fill="none">
    <circle cx="267" cy="216" r="171" stroke="currentColor" opacity=".25" />
    <circle cx="267" cy="216" r="143" stroke="currentColor" opacity=".2" />
    <path d="M125 364V204a140 140 0 0 1 280 0v160H125Z" fill="#d9ac73" />
    <path d="M182 364V205a83 83 0 0 1 166 0v159H182Z" fill="#f0dfc4" />
    <path d="M239 364V207a26 26 0 0 1 52 0v157h-52Z" fill="#782b38" />
    {Array.from({ length: 12 }, (_, i) => <path key={i} d={`M${125 + i * 25.45} 283v81`} stroke="#782b38" strokeWidth="1.2" />)}
    {[0, 1, 3, 4, 5, 7, 8, 10].map(i => <path key={i} d={`M${137.7 + i * 25.45} 283v49`} stroke="#782b38" strokeWidth="12" />)}
    <path d="M76 364h379" stroke="#e2bf91" strokeWidth="1.5" />
    <path d="M80 122c-1 18-4 21-21 23 17 1 20 4 21 22 2-18 5-21 22-22-17-2-20-5-22-23ZM421 218c-1 12-3 15-15 16 12 1 14 3 15 16 2-13 4-15 16-16-12-1-14-4-16-16Z" fill="#f0dfc4" />
    <path d="M352 54c19 8 35 20 48 36" stroke="#f0dfc4" /><path d="m394 89 7 2-1-7" stroke="#f0dfc4" />
    <text x="445" y="344" fill="#e2bf91" fontSize="10" letterSpacing="3" transform="rotate(-90 445 344)">СЛУШАТЬ. ЧУВСТВОВАТЬ. БЫТЬ ВМЕСТЕ.</text>
  </svg><span className="hero-art-caption">МЕСТО ВСТРЕЧИ — ГЕОРГИЕВСКИЙ ЗАЛ</span></div>;
}

function ConcertCard({ event, planned, togglePlan }) {
  const past = isPast(event);
  const [imageError, setImageError] = useState(false), [imageRetry, setImageRetry] = useState(0);
  useEffect(() => setImageError(false), [event.cover_url]);
  return <article className={`concert-card ${event.status === 'cancelled' ? 'cancelled-card' : ''}`}>
    <Link to={`/concert/${event.id}`} className="poster-link" aria-label={`Подробнее: ${event.title}`}><Poster event={event} retryKey={imageRetry} onImageError={() => setImageError(true)} showRetry={false} /><span className="poster-open"><Icon name="arrow" size={22} /></span></Link>
    {imageError && <p className="card-image-error" role="alert">Постер не загрузился. <button className="inline-button" onClick={() => { setImageError(false); setImageRetry(value => value + 1); }}>Повторить</button></p>}
    <div className="card-meta"><DateLine event={event} /><span className="age-limit">{event.age_limit ?? 0}+</span></div>
    <h3><Link to={`/concert/${event.id}`}>{event.title}</Link></h3>
    <p className="card-statistics">{averageRating(event) && <span>★ {averageRating(event)} / 5 · отзывов: {event.reviews_count}</span>}<span>Интересуются: {event.followers_count ?? 0}</span></p>
    <p className="card-description">{event.short_description || 'Встречаемся, чтобы услышать больше.'}</p>
    <div className="card-bottom"><span className="card-venue"><Icon name="pin" size={15} />{event.venue_names?.join(', ') || 'Площадка уточняется'}</span><button className={`save-button ${planned ? 'saved' : ''}`} aria-label={planned ? `Убрать из планов: ${event.title}` : `Хочу пойти: ${event.title}`} aria-pressed={planned} onClick={() => togglePlan(event.id)} disabled={!planned && (past || event.status === 'cancelled')} title={planned ? 'Убрать из моих планов' : past ? 'Концерт уже прошёл' : 'Сохранить в мои планы'}><Icon name="heart" size={19} fill={planned ? 'currentColor' : 'none'} /></button></div>
  </article>;
}

export default function Home({ onlyPlans, plans, togglePlan, openAuth, session }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const [query, setQuery] = useState('');
  const [period, setPeriod] = useState('all');
  const [month, setMonth] = useState('');
  const [visibleCount, setVisibleCount] = useState(9);
  const SectionTitle = onlyPlans ? 'h1' : 'h2';

  useEffect(() => {
    document.title = `${onlyPlans ? 'Мои планы' : 'Афиша'} — Музыкальный понедельник`;
    const controller = new AbortController();
    setLoading(true); setError('');
    api.concerts(controller.signal).then(setEvents).catch(error => { if (!controller.signal.aborted) setError(error.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [revision, onlyPlans]);
  useEffect(() => setVisibleCount(9), [query, period, month]);
  const filtered = useMemo(() => filterConcerts(events, { query, period, month, plannedIds: onlyPlans ? plans : undefined }), [events, query, period, month, onlyPlans, plans]);
  const months = useMemo(() => [...new Map(events.map(event => [monthKey(event.starts_at), { value: monthKey(event.starts_at), label: monthLabel(event.starts_at), date: event.starts_at }])).values()].sort((a, b) => new Date(a.date) - new Date(b.date)), [events]);
  const next = useMemo(() => events.filter(event => !isPast(event) && event.status !== 'cancelled').sort((a, b) => new Date(a.starts_at) - new Date(b.starts_at))[0], [events]);
  function reset() { setQuery(''); setPeriod('all'); setMonth(''); }

  return <>
    {!onlyPlans && <section className="hero container">
      <div className="hero-copy"><div className="eyebrow"><span className="tiny-star">✳</span> КЛУБ СЛУШАТЕЛЕЙ · ГЕОРГИЕВСКИЙ ЗАЛ</div><h1>У понедельника<br />есть <em>свой звук.</em></h1><p>Встречаемся на концертах.<br />Делимся впечатлениями. Находим своих.</p><a href="#afisha" className="hero-cta">Выбрать концерт<Icon name="arrow" size={19} /></a><span className="hero-edition">МУЗЫКАЛЬНЫЕ ПОНЕДЕЛЬНИКИ / КЛУБ</span></div>
      <HeroArt />
    </section>}
    {!onlyPlans && <div className="under-hero container"><span>Хорошая традиция — начинать неделю с музыки.</span>{next ? <Link to={`/concert/${next.id}`}><span>Ближайшая встреча</span><strong>{dateShort(next.starts_at)}</strong><Icon name="arrow" size={16} /></Link> : <span className="under-hero-note">До встречи в зале</span>}</div>}
    <section className="afisha-section container" id="afisha" aria-labelledby="afisha-title">
      <div className="section-heading"><div><div className="eyebrow">{onlyPlans ? 'ВАША ЛИЧНАЯ АФИША' : 'ВСТРЕЧИ, КОТОРЫЕ СТОИТ УСЛЫШАТЬ'}</div><SectionTitle id="afisha-title">{onlyPlans ? 'Мои планы' : 'Афиша концертов'}<span className="heading-dot">.</span></SectionTitle></div><span className="section-aside">{onlyPlans ? 'Сохраняются в этом браузере' : 'Живая музыка. Живое общение.'}</span></div>
      {onlyPlans && <p className="plans-privacy">Планы хранятся только в этом браузере, не видны другим и не увеличивают число подписчиков концерта.</p>}
      <div className="filters"><div className="period-tabs" role="group" aria-label="Период концертов">{[['all', 'Все концерты'], ['upcoming', 'Ближайшие'], ['past', 'Прошедшие']].map(([value, label]) => <button key={value} className={period === value ? 'selected' : ''} aria-pressed={period === value} onClick={() => setPeriod(value)}>{label}</button>)}</div>
        <div className="filter-fields"><label className="search-field"><Icon name="search" size={17} /><span className="sr-only">Поиск концертов</span><input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Название, исполнитель…" /></label><label className="month-field"><span className="sr-only">Месяц концерта</span><select value={month} onChange={event => setMonth(event.target.value)}><option value="">Все месяцы</option>{months.map(month => <option key={month.value} value={month.value}>{month.label}</option>)}</select></label></div>
      </div>
      {loading ? <div className="concert-grid" role="status" aria-label="Загружаем афишу">{[0, 1, 2].map(key => <div className="skeleton-card" key={key}><div className="skeleton poster" /><div className="skeleton skeleton-line" /><div className="skeleton skeleton-line short" /></div>)}</div> : error ? <ErrorState message={error} retry={() => setRevision(value => value + 1)} /> : !filtered.length ? <div className="empty-state"><span className="empty-icon"><Icon name={onlyPlans ? 'heart' : 'note'} size={28} /></span><h3>{query || month || period !== 'all' ? 'Пока ничего не нашлось' : onlyPlans ? 'Оставьте место для музыки' : 'Готовим следующую встречу'}</h3><p>{query || month || period !== 'all' ? 'Попробуйте другое название или выберите другой период.' : onlyPlans ? 'Нажмите на сердечко у понравившегося концерта — он появится здесь.' : 'Скоро здесь появятся концерты. Загляните чуть позже.'}</p>{query || month || period !== 'all' ? <button className="button secondary" onClick={reset}>Сбросить фильтры</button> : onlyPlans ? <Link className="button secondary" to="/">Посмотреть афишу<Icon name="arrow" /></Link> : <button className="button secondary" onClick={() => setRevision(value => value + 1)}><Icon name="refresh" size={16} />Обновить афишу</button>}</div> : <>
        <p className="results-count" aria-live="polite">{filtered.length === 1 ? '1 концерт' : `Концертов: ${filtered.length}`}</p>
        <div className="concert-grid">{filtered.slice(0, visibleCount).map(event => <ConcertCard key={event.id} event={event} planned={plans.includes(event.id)} togglePlan={togglePlan} />)}</div>
        {visibleCount < filtered.length && <div className="load-more"><button className="button secondary" onClick={() => setVisibleCount(count => count + 9)}>Ещё концерты<Icon name="arrow" /></button><span>Показано {visibleCount} из {filtered.length}</span></div>}
      </>}
    </section>
    {!onlyPlans && <section className="club-strip container"><span className="club-strip-symbol" aria-hidden="true">&</span><div><div className="eyebrow">СВОИ ЛЮДИ В СОСЕДНЕМ КРЕСЛЕ</div><h2>Вместе слушать интереснее.</h2><p>Обсудите программу, договоритесь о встрече<br className="desktop-break" /> и поделитесь тем, что осталось после концерта.</p></div>{session ? <Link to="/plans" className="button secondary">Открыть мои планы<Icon name="arrow" size={18} /></Link> : <button className="button secondary" onClick={openAuth}>Стать частью клуба<Icon name="arrow" size={18} /></button>}</section>}
  </>;
}
