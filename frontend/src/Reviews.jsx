import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from './api.js';
import { ErrorState, Icon, Modal } from './components.jsx';
import { canCreateReview, dateLong, participantName } from './utils.js';

function Stars({ rating }) {
  return <span className="review-stars" aria-label={`Оценка ${rating} из 5`}>{[1, 2, 3, 4, 5].map(value => <Icon key={value} name="star" size={15} fill={value <= rating ? 'currentColor' : 'none'} />)}</span>;
}

export default function Reviews({ concert, session, openAuth, notify }) {
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [offset, setOffset] = useState(0);
  const [exhausted, setExhausted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');
  const [formError, setFormError] = useState('');
  const [text, setText] = useState('');
  const [rating, setRating] = useState(0);
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const formRef = useRef(null);
  const alive = useRef(true);
  const ownReview = session && items.find(item => item.author_id === session.id);
  const canCreate = canCreateReview(concert);
  const closeDelete = useCallback(() => { if (!busy) setDeleting(null); }, [busy]);

  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; };
  }, []);

  const acceptPage = useCallback((result, append = false) => {
    setItems(old => append ? [...old, ...result.items.filter(item => !old.some(review => review.id === item.id))] : result.items);
    setStats(result.stats);
    setOffset(result.offset + result.items.length);
    setExhausted(result.items.length < result.limit);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    api.reviews(concert.id, 0, controller.signal).then(result => {
      if (!controller.signal.aborted) acceptPage(result);
    }).catch(error => { if (!controller.signal.aborted) setError(error.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [concert.id, revision, acceptPage]);

  useEffect(() => {
    setEditing(null);
    setText('');
    setRating(0);
    setFormError('');
  }, [session?.id]);

  async function loadMore() {
    setLoadingMore(true);
    setFormError('');
    try {
      const result = await api.reviews(concert.id, offset);
      if (alive.current) acceptPage(result, true);
    } catch (error) { if (alive.current) setFormError(error.message); }
    finally { if (alive.current) setLoadingMore(false); }
  }

  function edit(review) {
    setEditing(review.id);
    setText(review.text);
    setRating(review.rating);
    setFormError('');
    requestAnimationFrame(() => {
      formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      formRef.current?.querySelector('textarea')?.focus({ preventScroll: true });
    });
  }

  function cancelEdit() { setEditing(null); setText(''); setRating(0); setFormError(''); }

  async function submit(event) {
    event.preventDefault();
    if (!session || busy || loadingMore || !text.trim() || rating < 1) return;
    setBusy(true);
    setFormError('');
    try {
      const payload = { rating, text: text.trim() };
      if (editing) await api.updateReview(concert.id, editing, payload, session.token);
      else await api.createReview(concert.id, payload, session.token);
      if (!alive.current) return;
      notify(editing ? 'Отзыв изменён.' : 'Спасибо за ваш отзыв.');
      cancelEdit();
      setRevision(value => value + 1);
    } catch (error) { if (alive.current) setFormError(error.message); }
    finally { if (alive.current) setBusy(false); }
  }

  async function remove() {
    if (!deleting || !session || busy) return;
    setBusy(true);
    setFormError('');
    try {
      await api.deleteReview(concert.id, deleting.id, session.token);
      if (!alive.current) return;
      setDeleting(null);
      cancelEdit();
      notify('Отзыв удалён.');
      setRevision(value => value + 1);
    } catch (error) {
      if (alive.current) { setDeleting(null); setFormError(error.message); }
    } finally { if (alive.current) setBusy(false); }
  }

  return <section className="reviews-block" aria-labelledby="reviews-heading">
    <div className="reviews-title"><h2 id="reviews-heading">Отзывы слушателей</h2>
      {stats?.reviews_count > 0 && <div className="rating-summary"><Icon name="star" size={20} fill="currentColor" /><strong>{stats.avg_rating.toFixed(1)}</strong><span>из 5 · отзывов: {stats.reviews_count}</span></div>}
    </div>
    {loading ? <p className="muted" role="status">Загружаем отзывы…</p>
      : error ? <ErrorState compact message={error} retry={() => setRevision(value => value + 1)} />
        : <>
          {!items.length && <p className="reviews-empty">{canCreate ? 'Пока нет отзывов. Поделитесь первым впечатлением.' : 'Впечатления появятся здесь после концерта.'}</p>}
          <div className="reviews-list">{items.map(review => {
            const own = !!session && review.author_id === session.id;
            return <article className="review" key={review.id}>
              <div className="review-top"><strong>{own ? 'Ваш отзыв' : review.author_id ? participantName(review.author_id) : 'Удалённый пользователь'}</strong><Stars rating={review.rating} /></div>
              <p>{review.text}</p>
              <div className="review-bottom"><time dateTime={review.created_at}>{dateLong(review.created_at)}</time>
                {own && <div className="review-actions"><button className="inline-button" onClick={() => edit(review)} disabled={busy || loadingMore}>Изменить</button><button className="inline-button" onClick={() => setDeleting(review)} disabled={busy || loadingMore}>Удалить</button></div>}
              </div>
            </article>;
          })}</div>
          {!exhausted && offset < stats?.reviews_count && <button className="button secondary more-reviews" onClick={loadMore} disabled={loadingMore || busy}>{loadingMore ? 'Загружаем…' : 'Ещё отзывы'}</button>}
        </>}
    {formError && <p className="form-error" role="alert">{formError}</p>}
    {!loading && !error && <>
      {session && (editing || (canCreate && !ownReview)) ? <form className="review-form" onSubmit={submit} ref={formRef}>
        <h3>{editing ? 'Изменить свой отзыв' : 'Ваше впечатление'}</h3>
        <fieldset className="rating-input" disabled={busy}><legend>Ваша оценка</legend>{[1, 2, 3, 4, 5].map(value => <label key={value} className={value <= rating ? 'filled' : ''}><input type="radio" name="review-rating" value={value} checked={rating === value} onChange={() => setRating(value)} required /><span className="sr-only">{value} из 5</span><Icon name="star" size={27} fill={value <= rating ? 'currentColor' : 'none'} /></label>)}</fieldset>
        <label className="sr-only" htmlFor="review-text">Текст отзыва</label><textarea id="review-text" value={text} onChange={event => setText(event.target.value)} placeholder="Что вам запомнилось на концерте?" rows={4} required disabled={busy} />
        <div className="reviews-form-footer">{editing && <button type="button" className="text-button" onClick={cancelEdit} disabled={busy}>Отменить</button>}<button className="button" disabled={busy || loadingMore || !text.trim() || !rating}>{busy ? 'Сохраняем…' : editing ? 'Сохранить изменения' : 'Опубликовать отзыв'}</button></div>
      </form>
        : ownReview ? <p className="review-hint">Вы уже оставили отзыв. Его можно изменить или удалить выше.</p>
          : canCreate ? <div className="review-signin"><p>Поделитесь впечатлениями о концерте.</p><button className="button secondary" onClick={openAuth}>Войти и оставить отзыв<Icon name="arrow" size={16} /></button></div>
            : <p className="review-hint">{concert.status === 'cancelled' ? 'Для отменённого концерта публикация отзывов закрыта.' : 'Оставить отзыв можно после окончания концерта.'}</p>}
    </>}
    {deleting && <Modal title="Удалить свой отзыв?" onClose={closeDelete}><p className="modal-intro">Отзыв и оценка будут удалены. После этого можно будет написать новый отзыв.</p><div className="dialog-actions"><button className="button secondary" onClick={closeDelete} disabled={busy}>Отмена</button><button className="button" onClick={remove} disabled={busy}>{busy ? 'Удаляем…' : 'Удалить'}</button></div></Modal>}
  </section>;
}
