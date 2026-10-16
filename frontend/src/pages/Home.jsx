import { useEffect, useMemo, useState } from 'react';
import { api } from '../api.js';
import { DateLine, ErrorState, Icon, Link, Poster } from '../components.jsx';
import { dateShort, isPast } from '../utils.js';
import './Home.css';

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

export default function Home({ openAuth }) {
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    document.title = 'Афиша — Музыкальный понедельник';
    const controller = new AbortController();
    setLoading(true);
    setError('');
    api.concerts(page, controller.signal).then(data => {
      if (controller.signal.aborted) return;
      setEvents(old => page === 1 ? data.items : [...old, ...data.items.filter(item => !old.some(event => event.id === item.id))]);
      setTotal(data.total);
      if (data.items.length) {
        api.reviewStats(data.items.map(item => item.id), controller.signal).then(result => {
          if (!controller.signal.aborted) setStats(old => ({ ...old, ...Object.fromEntries(result.items.map(item => [item.afisha_id, item])) }));
        }).catch(() => { /* Statistics must not prevent visitors from opening posters. */ });
      }
    }).catch(error => { if (!controller.signal.aborted) setError(error.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [page, revision]);

  const next = useMemo(() => events
    .filter(event => !isPast(event) && event.status !== 'cancelled')
    .sort((a, b) => new Date(a.starts_at) - new Date(b.starts_at))[0], [events]);

  return <div className="home-page">
    <section className="hero container">
      <div className="hero-copy">
        <div className="eyebrow"><span className="tiny-star" aria-hidden="true">✳</span> КЛУБ СЛУШАТЕЛЕЙ · ГЕОРГИЕВСКИЙ ЗАЛ</div>
        <h1>У понедельника<br />есть <em>свой звук.</em></h1>
        <p>Встречаемся на концертах.<br />Делимся впечатлениями. Находим своих.</p>
        <a href="#afisha" className="hero-cta">Выбрать концерт<Icon name="arrow" size={19} /></a>
        <span className="hero-edition">МУЗЫКАЛЬНЫЕ ПОНЕДЕЛЬНИКИ / КЛУБ</span>
      </div>
      <HeroArt />
    </section>
    <div className="under-hero container">
      <span>Хорошая традиция — начинать неделю с музыки.</span>
      {next ? <Link to={`/concert/${next.id}`}><span>Ближайшая встреча</span><strong>{dateShort(next.starts_at)}</strong><Icon name="arrow" size={16} /></Link> : <span className="under-hero-note">До встречи в зале</span>}
    </div>
    <section className="container afisha-page" id="afisha" aria-labelledby="afisha-title">
    <div className="section-heading">
      <div><div className="eyebrow">ВСТРЕЧИ, КОТОРЫЕ СТОИТ УСЛЫШАТЬ</div><h2 id="afisha-title">Афиша концертов<span>.</span></h2></div>
      <span className="section-aside">Живая музыка. Живое общение.</span>
    </div>
    <div className="afisha-divider"><span>Все концерты</span>{!loading && !error && <span>Концертов: {total}</span>}</div>
    {loading && !events.length
      ? <div className="poster-grid" role="status" aria-label="Загружаем афишу">{[0, 1, 2].map(key => <div key={key}><div className="poster skeleton" /><div className="skeleton skeleton-line" /></div>)}</div>
      : !error && !events.length
        ? <div className="empty-state"><span className="empty-icon"><Icon name="note" size={30} /></span><h3>В афише пока тихо</h3><p>Концерты появятся здесь, когда организаторы добавят их в программу.</p></div>
        : <div className="poster-grid">{events.map(event => {
          const rating = stats[event.id];
          return <article className="concert-card" key={event.id}>
            <Link to={`/concert/${event.id}`} className="poster-link" aria-label={`Открыть концерт: ${event.title}`}>
              <Poster event={event} />
              <span className="poster-open"><span>О концерте</span><Icon name="arrow" size={22} /></span>
            </Link>
            <div className="card-meta"><DateLine event={event} /><span className="age-limit">{event.age_limit ?? 0}+</span></div>
            <h3><Link to={`/concert/${event.id}`}>{event.title}</Link></h3>
            {event.short_description && <p className="card-description">{event.short_description}</p>}
            <div className="card-bottom"><span className="card-venue"><Icon name="pin" size={16} />{event.venue_names?.join(', ') || 'Площадка уточняется'}</span>
              {rating?.reviews_count > 0 ? <span className="card-rating"><Icon name="star" size={14} />{rating.avg_rating.toFixed(1)}<span>({rating.reviews_count})</span></span> : isPast(event) && <span className="card-past">Состоялся</span>}
            </div>
          </article>;
        })}</div>}
    {error && <ErrorState message={error} retry={() => setRevision(value => value + 1)} />}
    {!!events.length && events.length < total && !error && <div className="load-more"><button className="button secondary" onClick={() => setPage(value => value + 1)} disabled={loading}>{loading ? 'Загружаем…' : 'Ещё концерты'}<Icon name="arrow" size={18} /></button><span>Показано {events.length} из {total}</span></div>}
    </section>
    <section className="club-strip container">
      <span className="club-strip-symbol" aria-hidden="true">&</span>
      <div><div className="eyebrow">СВОИ ЛЮДИ В СОСЕДНЕМ КРЕСЛЕ</div><h2>Вместе слушать интереснее.</h2><p>Обсудите программу, договоритесь о встрече<br className="desktop-break" /> и поделитесь тем, что осталось после концерта.</p></div>
      <button className="button secondary" onClick={openAuth}>Стать частью клуба<Icon name="arrow" size={18} /></button>
    </section>
  </div>;
}
