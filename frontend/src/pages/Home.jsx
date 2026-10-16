import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { DateLine, ErrorState, Icon, Link, Poster } from '../components.jsx';
import { isPast } from '../utils.js';

export default function Home() {
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

  return <section className="container afisha-page" aria-labelledby="afisha-title">
    <div className="afisha-heading">
      <div><div className="eyebrow">ГЕОРГИЕВСКИЙ ЗАЛ · КЛУБ СЛУШАТЕЛЕЙ</div><h1 id="afisha-title">Афиша<span>.</span></h1></div>
      <p>Выберите концерт.<br />Встретимся в зале и в обсуждении.</p>
    </div>
    {loading && !events.length
      ? <div className="poster-grid" role="status" aria-label="Загружаем афишу">{[0, 1].map(key => <div key={key}><div className="poster skeleton" /><div className="skeleton skeleton-line" /></div>)}</div>
      : !error && !events.length
        ? <div className="empty-state"><span className="empty-icon"><Icon name="note" size={30} /></span><h2>В афише пока тихо</h2><p>Концерты появятся здесь, когда организаторы добавят их в программу.</p></div>
        : <div className="poster-grid">{events.map(event => {
          const rating = stats[event.id];
          return <article className="concert-card" key={event.id}>
            <Link to={`/concert/${event.id}`} className="poster-link" aria-label={`Открыть концерт: ${event.title}`}>
              <Poster event={event} />
              <span className="poster-open"><span>О концерте</span><Icon name="arrow" size={22} /></span>
            </Link>
            <div className="card-meta"><DateLine event={event} /><span className="age-limit">{event.age_limit ?? 0}+</span></div>
            <h2><Link to={`/concert/${event.id}`}>{event.title}</Link></h2>
            {event.short_description && <p className="card-description">{event.short_description}</p>}
            <div className="card-bottom"><span className="card-venue"><Icon name="pin" size={16} />{event.venue_names?.join(', ') || 'Площадка уточняется'}</span>
              {rating?.reviews_count > 0 ? <span className="card-rating"><Icon name="star" size={14} />{rating.avg_rating.toFixed(1)}<span>({rating.reviews_count})</span></span> : isPast(event) && <span className="card-past">Состоялся</span>}
            </div>
          </article>;
        })}</div>}
    {error && <ErrorState message={error} retry={() => setRevision(value => value + 1)} />}
    {!!events.length && events.length < total && !error && <div className="load-more"><button className="button secondary" onClick={() => setPage(value => value + 1)} disabled={loading}>{loading ? 'Загружаем…' : 'Ещё концерты'}<Icon name="arrow" size={18} /></button><span>Показано {events.length} из {total}</span></div>}
  </section>;
}
