import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { ErrorState, Icon, Link, Poster } from '../components.jsx';
import Discussion from '../Discussion.jsx';
import Reviews from '../Reviews.jsx';
import { dateLong, isPast, time, weekday } from '../utils.js';

export default function Concert({ id, session, openAuth, notify }) {
  const [concert, setConcert] = useState(null);
  const [venues, setVenues] = useState([]);
  const [venueLoading, setVenueLoading] = useState(false);
  const [venueError, setVenueError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    setVenues([]);
    setVenueError(false);
    api.concert(id, controller.signal).then(data => {
      if (controller.signal.aborted) return;
      setConcert(data);
      document.title = `${data.title} — Музыкальный понедельник`;
      setVenueLoading(true);
      Promise.allSettled(data.venue_ids.map(venueId => api.venue(venueId, controller.signal))).then(results => {
        if (controller.signal.aborted) return;
        setVenues(results.filter(result => result.status === 'fulfilled').map(result => result.value));
        setVenueError(results.some(result => result.status === 'rejected'));
        setVenueLoading(false);
      });
    }).catch(error => { if (!controller.signal.aborted) setError(error.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [id, revision]);

  if (loading) return <div className="container concert-loading" role="status" aria-label="Загружаем концерт"><div className="skeleton skeleton-line" /><div className="skeleton skeleton-title" /><div className="detail-layout"><div className="poster skeleton" /><div className="skeleton skeleton-panel" /></div></div>;
  if (error) return <div className="container error-page"><Link to="/" className="back-link"><Icon name="back" size={17} />К афише</Link><ErrorState message={error} retry={() => setRevision(value => value + 1)} /></div>;
  if (!concert) return null;
  const past = isPast(concert);
  const cancelled = concert.status === 'cancelled';
  const cover = concert.images?.find(image => image.is_cover) || concert.images?.[0];

  return <div className="container concert-page">
    <Link to="/" className="back-link"><Icon name="back" size={17} />Все концерты</Link>
    <div className="concert-title"><div className="concert-kicker"><div className="eyebrow">МУЗЫКАЛЬНЫЕ ПОНЕДЕЛЬНИКИ{past ? ' / КОНЦЕРТ СОСТОЯЛСЯ' : ''}</div><span className="age-limit">{concert.age_limit ?? 0}+</span></div><h1>{concert.title}</h1>{concert.short_description && <p>{concert.short_description}</p>}</div>
    <div className="detail-layout">
      <div className="concert-main">
        <section className="event-block" aria-label="О концерте">
          <Poster event={concert} featured />
          <div className="event-details">
            <div className="event-facts">
              <div><Icon name="calendar" size={22} /><span><strong>{dateLong(concert.starts_at)}</strong><small>{weekday(concert.starts_at)}</small></span></div>
              <div><Icon name="clock" size={22} /><span><strong>{time(concert.starts_at)} — {time(concert.ends_at)}</strong><small>время московское</small></span></div>
            </div>
            {venues.map(venue => <div className="venue-fact" key={venue.id}><Icon name="pin" size={22} /><span><strong>{venue.name}</strong><small>{venue.city}, {venue.address}</small></span></div>)}
            {venueLoading && <p className="muted small-text" role="status">Загружаем площадку…</p>}
            {venueError && <p className="muted small-text">Не удалось загрузить часть информации о площадке. <button className="inline-button" onClick={() => setRevision(value => value + 1)}>Повторить</button></p>}
            {cancelled && <div className="notice cancelled-notice">Концерт отменён. Обсуждение остаётся открытым.</div>}
            <div className="description-block"><h2>О концерте</h2>
              {concert.description ? concert.description.split(/\n\s*\n/).filter(Boolean).map((paragraph, index) => <p key={index}>{paragraph}</p>) : <p className="muted">Подробная программа пока не опубликована.</p>}
            </div>
            {concert.images?.length > 1 && <div className="extra-images">{concert.images.filter(image => image.id !== cover.id).map(image => <Poster key={image.id} event={{ ...concert, images: [image] }} />)}</div>}
          </div>
        </section>
        <Reviews concert={concert} session={session} openAuth={openAuth} notify={notify} />
      </div>
      <aside className="discussion-aside"><Discussion id={id} session={session} openAuth={openAuth} /></aside>
    </div>
  </div>;
}
