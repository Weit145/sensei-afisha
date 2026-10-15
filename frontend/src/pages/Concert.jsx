import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../api.js';
import { ErrorState, Icon, Link, Poster } from '../components.jsx';
import { dateLong, dateShort, hash, initials, isPast, participantName, time, weekday } from '../utils.js';

function Discussion({ id, session, openAuth }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sending, setSending] = useState(false);
  const [text, setText] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [pollError, setPollError] = useState('');
  const listRef = useRef(null);
  const initialScroll = useRef(true);
  const shouldScroll = useRef(true);

  useEffect(() => {
    const controller = new AbortController();
    let timer;
    let active = true;
    async function load(initial = false) {
      if (initial) { setLoading(true); setError(''); }
      try {
        const result = await api.messages(id, controller.signal);
        if (!active) return;
        const list = listRef.current;
        shouldScroll.current = initialScroll.current || !list || list.scrollHeight - list.scrollTop - list.clientHeight < 70;
        setMessages(previous => {
          const byId = new Map(previous.map(message => [message.id, message]));
          for (const message of result.items) byId.set(message.id, message);
          return [...byId.values()].sort((a, b) => new Date(a.created_at) - new Date(b.created_at) || a.id.localeCompare(b.id));
        });
        setError(''); setPollError(''); initialScroll.current = false;
      } catch (error) { if (active) { if (initial) setError(error.message); else setPollError('Обновление приостановлено. Повторим подключение автоматически.'); } }
      finally {
        if (active) { setLoading(false); timer = setTimeout(() => { if (!document.hidden) load(); else timer = setTimeout(() => load(), 15000); }, 10000); }
      }
    }
    load(true);
    return () => { active = false; clearTimeout(timer); controller.abort(); };
  }, [id, refresh]);
  useEffect(() => { if (shouldScroll.current && listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight; }, [messages]);

  async function send(event) {
    event.preventDefault();
    if (!session || !text.trim() || sending) return;
    setSending(true); setPollError('');
    try {
      const message = await api.sendMessage(id, text.trim(), session.token);
      shouldScroll.current = true;
      setMessages(old => [...old.filter(item => item.id !== message.id), message].sort((a, b) => new Date(a.created_at) - new Date(b.created_at) || a.id.localeCompare(b.id)));
      setText('');
    } catch (error) { setPollError(error.message); }
    finally { setSending(false); }
  }

  return <section className="discussion-panel" aria-labelledby="discussion-heading" id="discussion">
    <div className="discussion-heading"><div><Icon name="chat" size={22} /><h2 id="discussion-heading">Обсуждение</h2>{!loading && <span className="message-count">{messages.length}</span>}</div><button className="icon-button" onClick={() => setRefresh(value => value + 1)} disabled={loading} aria-label="Обновить обсуждение" title="Обновить"><Icon name="refresh" size={17} /></button></div>
    <div className="discussion-subtitle">Найдите компанию. Поделитесь ожиданиями.</div>
    <div className="messages-list" ref={listRef} role="log" aria-label="Сообщения обсуждения" aria-live="polite" aria-relevant="additions text" tabIndex={0}>
      {loading ? <p className="discussion-loading" role="status">Загружаем разговор…</p> : error ? <ErrorState compact message={error} retry={() => setRefresh(value => value + 1)} /> : !messages.length ? <div className="conversation-empty"><span className="conversation-drawing" aria-hidden="true"><Icon name="chat" size={44} /><span>♪</span></span><h3>Займите первое кресло.</h3><p>Кто идёт на концерт?<br />Самое время познакомиться.</p></div> : messages.map((message, index) => {
        const own = message.author_id === session?.id;
        const name = own ? 'Вы' : participantName(message.author_id);
        const dayChanged = index === 0 || dateLong(message.created_at) !== dateLong(messages[index - 1].created_at);
        return <div key={message.id}>{dayChanged && <div className="chat-date">{dateShort(message.created_at)}</div>}<article className={`message ${own ? 'own-message' : ''}`}><span className={`avatar avatar-${hash(message.author_id) % 4}`} aria-hidden="true">{own ? 'ВЫ' : initials(name.split(' ')[1])}</span><div className="message-body"><div className="message-meta"><strong>{name}</strong><time dateTime={message.created_at}>{time(message.created_at)}</time></div><p>{message.text}</p></div></article></div>;
      })}
    </div>
    <form className="message-form" onSubmit={send}>
      {pollError && <p className="form-error" role="alert">{pollError}</p>}
      <label className="sr-only" htmlFor="new-message">Новое сообщение</label><textarea id="new-message" value={text} onChange={event => setText(event.target.value)} placeholder={session ? 'О чём хочется поговорить?' : 'Присоединитесь к разговору…'} rows={3} maxLength={2000} disabled={!session || sending} onKeyDown={event => { if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) { event.preventDefault(); event.currentTarget.form.requestSubmit(); } }} />
      <div className="message-form-bottom">{session ? <><span>{text.length}/2000</span><button className="button" disabled={!text.trim() || sending}>{sending ? 'Отправляем…' : 'Отправить'}<Icon name="send" size={16} /></button></> : <><span>Для сообщений нужен вход в клуб</span><button type="button" className="button" onClick={openAuth}>Войти<Icon name="arrow" size={16} /></button></>}</div>
    </form>
  </section>;
}

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
        <p className="local-plans-note">Ваши планы сохраняются только в этом браузере и не видны другим участникам.</p>
        <div className="description-block"><h2>О концерте</h2>{concert.description ? concert.description.split(/\n\s*\n/).filter(Boolean).map((paragraph, i) => <p key={i}>{paragraph}</p>) : <p className="muted">Подробная программа пока не опубликована. Следите за обновлениями.</p>}</div>
        {concert.images?.length > 1 && <div className="extra-images">{concert.images.filter(image => image.id !== (concert.images.find(image => image.is_cover) || concert.images[0]).id).map(image => <Poster key={image.id} event={{ ...concert, images: [image] }} />)}</div>}
      </div></section>
      <section className="reviews-block" aria-labelledby="reviews-heading"><div className="reviews-title"><h2 id="reviews-heading">После последнего аккорда</h2><span className="coming-soon">СКОРО</span></div><p className="muted">Место для ваших впечатлений о концерте.</p><div className="reviews-empty"><Icon name="star" size={28} /><div><h3>Здесь будут отзывы слушателей.</h3><p>Публикация отзывов пока недоступна.<br />А поделиться впечатлениями уже можно в обсуждении.</p><a className="inline-button" href="#discussion">Перейти к обсуждению<Icon name="arrow" size={15} /></a></div></div><label className="sr-only" htmlFor="review-draft">Отзыв — публикация пока недоступна</label><textarea id="review-draft" placeholder="Что вам запомнилось?" rows={3} disabled /><div className="reviews-form-footer"><span>Возможность готовится к открытию</span><button className="button secondary" disabled>Оставить отзыв</button></div></section>
    </div><aside className="discussion-aside"><Discussion id={id} session={session} openAuth={openAuth} /><p className="discussion-footnote">Знакомьтесь, договаривайтесь о встрече<br />и будьте внимательны друг к другу.</p></aside></div>
  </div>;
}
