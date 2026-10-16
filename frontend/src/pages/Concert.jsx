import { useCallback, useEffect, useState } from 'react';
import { api } from '../api.js';
import { ErrorState, Icon, Link, Poster } from '../components.jsx';
import Discussion from '../Discussion.jsx';
import Reviews from '../Reviews.jsx';
import { averageRating, dateLong, isPast, time, weekday } from '../utils.js';

export default function Concert({ id, plans, togglePlan, session, openAuth, notify }) {
  const [concert, setConcert] = useState(null);
  const [venues, setVenues] = useState([]);
  const [venueError, setVenueError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const planned = plans.includes(id);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(''); setVenueError(false);
    api.concert(id, controller.signal).then(async data => {
      if (controller.signal.aborted) return;
      setConcert(data); document.title = `${data.title} — Музыкальный понедельник`;
      const results = await Promise.allSettled(data.venue_ids.map(venueId => api.venue(venueId, controller.signal)));
      if (!controller.signal.aborted) {
        setVenues(results.filter(result => result.status === 'fulfilled').map(result => result.value));
        setVenueError(results.some(result => result.status === 'rejected'));
      }
    }).catch(error => { if (!controller.signal.aborted) setError(error.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [id, revision]);

  const share = useCallback(async () => {
    try { await navigator.clipboard.writeText(location.href); notify('Ссылка на концерт скопирована.'); }
    catch { notify('Скопируйте ссылку на концерт из адресной строки браузера.'); }
  }, [notify]);

  if (loading) return <div className="container concert-loading" role="status" aria-label="Загружаем концерт"><div className="skeleton skeleton-line short" /><div className="skeleton skeleton-title" /><div className="detail-layout"><div className="skeleton poster" /><div className="skeleton poster" /></div></div>;
  if (error) return <div className="container error-page"><Link to="/" className="back-link"><Icon name="back" size={16} />К афише</Link><ErrorState message={error} retry={() => setRevision(value => value + 1)} /></div>;
  if (!concert) return null;
  const past = isPast(concert);
  const cancelled = concert.status === 'cancelled';
  return <div className="container concert-page">
    <div className="detail-topline"><Link to="/" className="back-link"><Icon name="back" size={16} />Все концерты</Link><button className="text-button" onClick={share}><Icon name="share" size={17} />Поделиться</button></div>
    <div className="concert-title"><div className="eyebrow">МУЗЫКАЛЬНЫЕ ПОНЕДЕЛЬНИКИ{past ? ' / ПРОШЕДШИЙ КОНЦЕРТ' : ''}</div><h1>{concert.title}</h1><p>{concert.short_description}</p></div>
    <div className="detail-layout"><div className="concert-main">
      <section className="event-block" aria-label="О концерте"><Poster event={concert} featured /><div className="event-details">
        <div className="event-facts"><div><Icon name="calendar" size={21} /><span><strong>{dateLong(concert.starts_at)}</strong><small>{weekday(concert.starts_at)}</small></span></div><div><Icon name="clock" size={21} /><span><strong>{time(concert.starts_at)} — {time(concert.ends_at)}</strong><small>время московское</small></span></div><span className="age-badge">{concert.age_limit ?? 0}+</span></div>
        {venues.map(venue => <div className="venue-fact" key={venue.id}><Icon name="pin" size={21} /><span><strong>{venue.name}</strong><small>{venue.city}, {venue.address}</small></span></div>)}
        {venueError && <p className="muted small-text">Не удалось загрузить часть информации о площадке. <button className="inline-button" onClick={() => setRevision(value => value + 1)}>Повторить</button></p>}
        {cancelled && <div className="notice cancelled-notice">Концерт отменён. Обсуждение остаётся открытым.</div>}
        {!cancelled && past && <div className="notice">Этот концерт уже прошёл. Обсудите его с другими слушателями.</div>}
        <div className="attendance-row"><button className={`button attendance-button ${planned ? 'is-planned' : ''}`} onClick={() => togglePlan(id)} disabled={!planned && (past || cancelled)} aria-pressed={planned}><Icon name={planned ? 'check' : 'heart'} size={19} />{planned ? 'В моих планах' : 'Хочу пойти'}</button><a href="#discussion" className="text-button">Найти компанию<Icon name="arrow" size={17} /></a></div>
        <p className="concert-statistics">{averageRating(concert) && <span>★ {averageRating(concert)} / 5 · отзывов: {concert.reviews_count}</span>}<span>Интересуются: {concert.followers_count ?? 0}</span></p>
        <p className="local-plans-note">Ваши планы сохраняются только в этом браузере и не видны другим участникам.</p>
        <div className="description-block"><h2>О концерте</h2>{concert.description ? concert.description.split(/\n\s*\n/).filter(Boolean).map((paragraph, i) => <p key={i}>{paragraph}</p>) : <p className="muted">Подробная программа пока не опубликована. Следите за обновлениями.</p>}</div>
        {concert.images?.length > 1 && <div className="extra-images">{concert.images.filter(image => image.id !== (concert.images.find(image => image.is_cover) || concert.images[0]).id).map(image => <Poster key={image.id} event={{ ...concert, images: [image] }} />)}</div>}
      </div></section>
      <Reviews concert={concert} session={session} openAuth={openAuth} notify={notify} onStats={stats => setConcert(current => ({ ...current, rating_sum: stats.rating_sum, reviews_count: stats.reviews_count }))} />
    </div><aside className="discussion-aside"><Discussion id={id} session={session} openAuth={openAuth} /><p className="discussion-footnote">Знакомьтесь, договаривайтесь о встрече<br />и будьте внимательны друг к другу.</p></aside></div>
  </div>;
}
