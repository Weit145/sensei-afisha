import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from './api.js';
import { ErrorState, Icon, Modal } from './components.jsx';
import { averageRating, canCreateReview, dateLong, participantName } from './utils.js';

export default function Reviews({ concert, session, openAuth, onStats, notify, onContact, refreshKey = 0 }) {
  const [data, setData] = useState(null), [loading, setLoading] = useState(true), [error, setError] = useState('');
  const [revision, setRevision] = useState(0), [visible, setVisible] = useState(10);
  const [rating, setRating] = useState(5), [text, setText] = useState(''), [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false), [actionError, setActionError] = useState(''), [deleting, setDeleting] = useState(null);
  const [now, setNow] = useState(Date.now);
  const controllerRef = useRef(null), formRef = useRef(null);
  const mutationControllerRef = useRef(null), dataRef = useRef(data); dataRef.current = data;
  const statsRef = useRef(onStats); statsRef.current = onStats;
  const closeDelete = useCallback(() => { if (!busy) setDeleting(null); }, [busy]);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 30000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    setEditing(null); setText(''); setRating(5); setActionError(''); setDeleting(null);
  }, [session?.id]);
  useEffect(() => {
    const controller = new AbortController(); mutationControllerRef.current = controller;
    return () => controller.abort();
  }, [concert.id]);
  useEffect(() => {
    const controller = new AbortController(); controllerRef.current = controller;
    if (!dataRef.current) setLoading(true);
    setError('');
    api.reviews(concert.id, controller.signal).then(result => {
      if (!controller.signal.aborted) { setData(result); statsRef.current(result.stats); }
    }).catch(error => { if (!controller.signal.aborted) setError(error.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [concert.id, revision, refreshKey]);

  const own = data?.items.find(item => item.author_id === session?.id);
  const orderedReviews = own ? [own, ...data.items.filter(item => item.id !== own.id)] : data?.items;
  const eligible = canCreateReview(concert, now);
  async function mutate(operation, message) {
    const signal = mutationControllerRef.current.signal;
    setBusy(true); setActionError('');
    try {
      await operation(signal);
      if (signal.aborted) return;
      setEditing(null); setText(''); setRating(5); setDeleting(null); notify(message);
      setRevision(value => value + 1);
    } catch (error) { if (!signal.aborted) setActionError(error.message); }
    finally { if (!signal.aborted) setBusy(false); }
  }
  function submit(event) {
    event.preventDefault();
    if (!session || !text.trim() || busy) return;
    const body = { rating: Number(rating), text: text.trim() };
    mutate(signal => editing ? api.updateReview(concert.id, editing, body, signal) : api.createReview(concert.id, body, signal), editing ? 'Отзыв обновлён.' : 'Спасибо за ваши впечатления.');
  }
  function edit(review) {
    setEditing(review.id); setText(review.text); setRating(review.rating); setActionError('');
    requestAnimationFrame(() => formRef.current?.querySelector('textarea')?.focus());
  }
  return <section className="reviews-block" aria-labelledby="reviews-heading">
    <div className="reviews-title"><h2 id="reviews-heading">После последнего аккорда</h2><Icon name="star" size={23} /></div>
    <p className="review-summary" aria-live="polite">{data ? averageRating(data.stats) ? <><strong>{averageRating(data.stats)} / 5</strong><span>Отзывов: {data.stats.reviews_count}</span></> : 'Оценок пока нет' : 'Впечатления слушателей'}</p>
    {loading ? <p className="small-text muted" role="status">Загружаем отзывы…</p> : error ? <ErrorState compact message={error} retry={() => setRevision(value => value + 1)} /> : <>
      {!data?.items.length ? <div className="reviews-empty"><Icon name="star" size={28} /><div><h3>У каждого — своё послезвучие.</h3><p>Здесь пока нет отзывов.</p></div></div> : <div className="review-list">{orderedReviews.slice(0, visible).map(review => <article className="review-item" key={review.id}><div className="review-meta">{review.author_id ? <button className="author-contact" onClick={() => onContact(review.author_id)} aria-label={`Открыть контакты: ${review.author_id === session?.id ? session.username : review.nickname || participantName(review.author_id)}`}>{review.author_id === session?.id ? 'Ваш отзыв' : review.nickname || participantName(review.author_id)}<Icon name="external" size={12} /></button> : <strong>Удалённый участник</strong>}<span aria-label={`Оценка ${review.rating} из 5`}>{'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}</span><time dateTime={review.created_at}>{dateLong(review.created_at)}</time></div><p>{review.text}</p>{session && review.author_id === session.id && <div className="review-actions"><button className="inline-button" disabled={busy} onClick={() => edit(review)}>Редактировать</button><button className="inline-button" disabled={busy} onClick={() => setDeleting(review)}>Удалить</button></div>}</article>)}</div>}
      {data?.items.length > visible && <button className="inline-button" onClick={() => setVisible(count => count + 10)}>Ещё отзывы</button>}
      {editing || (!own && eligible && session) ? <form className="form-stack review-form" onSubmit={submit} ref={formRef} aria-busy={busy}>
        <h3>{editing ? 'Ваш отзыв — новая редакция' : 'Что осталось после концерта?'}</h3>
        <fieldset className="rating-field" disabled={busy}><legend>Ваша оценка</legend>{[1, 2, 3, 4, 5].map(value => <label key={value}><input type="radio" name="rating" value={value} checked={Number(rating) === value} onChange={() => setRating(value)} /><span>{value} ★</span></label>)}</fieldset>
        <label>Впечатления<textarea value={text} onChange={event => setText(event.target.value)} rows={4} required disabled={busy} placeholder="Что вам запомнилось?" /></label>
        <div className="review-actions"><button className="button" disabled={busy || !text.trim()}>{busy ? 'Сохраняем…' : editing ? 'Сохранить отзыв' : 'Оставить отзыв'}</button>{editing && <button type="button" className="inline-button" disabled={busy} onClick={() => { setEditing(null); setText(''); }}>Отменить</button>}</div>
      </form> : concert.status === 'cancelled' ? <p className="notice">Для отменённого концерта новые отзывы недоступны.</p> : !eligible ? <p className="notice">Оставить отзыв можно после окончания опубликованного концерта.</p> : !session ? <p className="notice">Поделитесь впечатлениями: <button className="inline-button" onClick={openAuth}>войдите в клуб</button>.</p> : <p className="notice">Спасибо, ваш отзыв опубликован. Его можно отредактировать или удалить.</p>}
    </>}
    {actionError && <p className="form-error" role="alert">{actionError} <button className="inline-button" disabled={busy} onClick={() => setRevision(value => value + 1)}>Обновить отзывы</button></p>}
    {deleting && <Modal title="Удалить ваш отзыв?" onClose={closeDelete}><p className="modal-intro">Текст и оценка будут удалены. Позже вы сможете написать новый отзыв.</p>{actionError && <p className="form-error" role="alert">{actionError}</p>}<div className="review-actions"><button className="button" disabled={busy} onClick={() => mutate(signal => api.deleteReview(concert.id, deleting.id, signal), 'Отзыв удалён.')}>{busy ? 'Удаляем…' : 'Удалить отзыв'}</button><button className="inline-button" disabled={busy} onClick={closeDelete}>Оставить</button></div></Modal>}
  </section>;
}
