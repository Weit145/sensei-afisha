import { useCallback, useEffect, useRef, useState } from 'react';
import { api, mediaUrl } from '../api.js';
import { ErrorState, Icon, Link, Modal } from '../components.jsx';
import { dateLong } from '../utils.js';
import { concertPayload, moscowInput, validateImages, venuePayload } from '../adminUtils.js';

const emptyConcert = { title: '', short_description: '', description: '', starts_at: '', ends_at: '', venue_ids: [], age_limit: '0', status: 'published' };
const emptyVenue = { name: '', city: '', address: '', latitude: '', longitude: '' };
const imageAccept = 'image/jpeg,image/png,image/gif,image/webp,.jpg,.jpeg,.png,.gif,.webp';

function Editor({ kind, id, venues, venuesError, reloadVenues, onClose, onSaved, notify }) {
  const isConcert = kind === 'concert';
  const [recordId, setRecordId] = useState(id), [record, setRecord] = useState(null);
  const [form, setForm] = useState(isConcert ? emptyConcert : emptyVenue);
  const [files, setFiles] = useState([]), [imageFile, setImageFile] = useState(null), [imageKey, setImageKey] = useState(0);
  const [loading, setLoading] = useState(Boolean(id)), [busy, setBusy] = useState(false), [error, setError] = useState(''), [revision, setRevision] = useState(0);
  const [status, setStatus] = useState('');
  const controllerRef = useRef(null);
  const close = useCallback(() => { if (!busy) onClose(); }, [busy, onClose]);
  useEffect(() => {
    const controller = new AbortController(); controllerRef.current = controller;
    if (id) {
      setLoading(true); setError('');
      (isConcert ? api.concert(id, controller.signal) : api.venue(id, controller.signal)).then(result => {
        if (controller.signal.aborted) return;
        setRecord(result);
        setForm(isConcert ? { ...result, short_description: result.short_description || '', description: result.description || '', starts_at: moscowInput(result.starts_at), ends_at: moscowInput(result.ends_at), age_limit: result.age_limit ?? '' } : { ...result, latitude: result.latitude ?? '', longitude: result.longitude ?? '' });
      }).catch(error => { if (!controller.signal.aborted) setError(error.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }
    return () => controller.abort();
  }, [id, isConcert, revision]);
  const change = (field, value) => setForm(old => ({ ...old, [field]: value }));
  async function save(event) {
    event.preventDefault(); setBusy(true); setError(''); setStatus('');
    const signal = controllerRef.current.signal;
    try {
      const body = isConcert ? concertPayload(form) : venuePayload(form);
      if (isConcert && !recordId) await validateImages(files);
      signal.throwIfAborted();
      const result = isConcert ? recordId ? await api.updateConcert(recordId, body, signal) : await api.createConcert(body, files, signal) : recordId ? await api.updateVenue(recordId, body, signal) : await api.createVenue(body, signal);
      if (signal.aborted) return;
      setRecordId(result.id); setRecord(result); setFiles([]); onSaved(); notify(isConcert ? 'Афиша сохранена.' : 'Площадка сохранена.');
      setStatus(isConcert ? 'Афиша сохранена.' : 'Площадка сохранена.');
      if (!isConcert) onClose();
    } catch (error) { if (!signal.aborted) setError(error.message); }
    finally { if (!signal.aborted) setBusy(false); }
  }
  async function imageAction(operation) {
    const signal = controllerRef.current.signal;
    setBusy(true); setError(''); setStatus('');
    try {
      await operation(signal);
      if (signal.aborted) return;
      setImageFile(null); setImageKey(value => value + 1); onSaved();
      const result = await api.concert(recordId, signal);
      if (!signal.aborted) { setRecord(result); setStatus('Изображения обновлены.'); notify('Изображения обновлены.'); }
    } catch (error) { if (!signal.aborted) setError(error.message); }
    finally { if (!signal.aborted) setBusy(false); }
  }
  return <Modal title={isConcert ? recordId ? 'Редактируем афишу.' : 'Новая встреча с музыкой.' : recordId ? 'Редактируем площадку.' : 'Новое место встречи.'} onClose={close} className="admin-modal">
    <p className="modal-intro">{isConcert ? 'Программа, место и время — всё, что нужно слушателю.' : 'Площадка будет доступна при создании и редактировании афиш.'}</p>
    {loading ? <p role="status">Загружаем запись…</p> : id && !record ? <ErrorState compact message={error} retry={() => setRevision(value => value + 1)} /> : <>
      <form className="form-stack admin-form" onSubmit={save} aria-busy={busy}>
        <fieldset disabled={busy} className="form-fields">
          {isConcert ? <>
            <label>Название концерта<input required maxLength={255} value={form.title} onChange={event => change('title', event.target.value)} /></label>
            <label>Короткое описание<textarea rows={2} value={form.short_description} onChange={event => change('short_description', event.target.value)} /></label>
            <label>Полная программа и описание<textarea rows={5} value={form.description} onChange={event => change('description', event.target.value)} /></label>
            <div className="form-columns"><label>Начало · московское время<input type="datetime-local" required value={form.starts_at} onChange={event => change('starts_at', event.target.value)} /></label><label>Окончание · московское время<input type="datetime-local" required value={form.ends_at} onChange={event => change('ends_at', event.target.value)} /></label></div>
            <fieldset className="venue-choices"><legend>Площадка · выберите хотя бы одну</legend>{venuesError ? <p className="form-error" role="alert">{venuesError} <button type="button" className="inline-button" onClick={reloadVenues}>Повторить</button></p> : venues.length ? venues.map(venue => <label key={venue.id}><input type="checkbox" checked={form.venue_ids.includes(venue.id)} onChange={event => change('venue_ids', event.target.checked ? [...form.venue_ids, venue.id] : form.venue_ids.filter(value => value !== venue.id))} /><span>{venue.name}<small>{venue.city}, {venue.address}</small></span></label>) : <p className="small-text muted">Сначала добавьте площадку в разделе «Площадки».</p>}</fieldset>
            <div className="form-columns"><label>Статус<select value={form.status} onChange={event => change('status', event.target.value)}><option value="published">Опубликован</option><option value="cancelled">Отменён</option></select></label><label>Возрастное ограничение<select value={form.age_limit} onChange={event => change('age_limit', event.target.value)}><option value="">Не указано</option>{[0, 6, 12, 16, 18].map(age => <option key={age} value={age}>{age}+</option>)}</select></label></div>
            {!recordId && <label>Постеры · JPEG, PNG, GIF, WebP<input type="file" accept={imageAccept} multiple onChange={event => setFiles([...event.target.files])} /><small>Первое изображение станет обложкой. Изображения можно добавить и после создания.</small></label>}
          </> : <>
            <label>Название площадки<input required maxLength={255} value={form.name} onChange={event => change('name', event.target.value)} /></label>
            <label>Город<input required maxLength={100} value={form.city} onChange={event => change('city', event.target.value)} /></label>
            <label>Адрес<input required maxLength={500} value={form.address} onChange={event => change('address', event.target.value)} /></label>
            <div className="form-columns"><label>Широта · необязательно<input type="number" step="any" min={-90} max={90} value={form.latitude} onChange={event => change('latitude', event.target.value)} /></label><label>Долгота · необязательно<input type="number" step="any" min={-180} max={180} value={form.longitude} onChange={event => change('longitude', event.target.value)} /></label></div>
          </>}
        </fieldset>
        {error && <p className="form-error" role="alert">{error}</p>}
        <p className="editor-status" role="status">{status}</p>
        <div className="editor-actions"><button className="button" disabled={busy || (isConcert && (!venues.length || Boolean(venuesError)))}>{busy ? 'Сохраняем…' : recordId ? 'Сохранить изменения' : isConcert ? 'Создать афишу' : 'Создать площадку'}<Icon name="check" size={17} /></button><button type="button" className="inline-button" disabled={busy} onClick={close}>Закрыть</button></div>
      </form>
      {isConcert && recordId && <section className="image-editor" aria-labelledby="images-title"><h3 id="images-title">Постеры концерта</h3><p className="small-text muted">Обложка видна в афише. Остальные изображения — на странице концерта.</p>
        {!record?.images?.length ? <p className="notice">Изображений пока нет.</p> : <div className="admin-images">{record.images.map(image => <article key={image.id}><img src={mediaUrl(image.image_url)} alt={image.is_cover ? 'Обложка концерта' : 'Постер концерта'} /><div>{image.is_cover ? <strong>Обложка</strong> : <button className="inline-button" disabled={busy} onClick={() => imageAction(signal => api.coverImage(recordId, image.id, signal))}>На обложку</button>}<button className="inline-button" disabled={busy} onClick={() => imageAction(signal => api.deleteImage(recordId, image.id, signal))}>Удалить изображение</button></div></article>)}</div>}
        <form className="form-stack" onSubmit={event => { event.preventDefault(); if (imageFile) imageAction(async signal => { await validateImages([imageFile]); signal.throwIfAborted(); await api.addImage(recordId, imageFile, signal); }); }}>
          <label>Добавить один постер · JPEG, PNG, GIF, WebP<input key={imageKey} type="file" accept={imageAccept} required disabled={busy} onChange={event => setImageFile(event.target.files[0] || null)} /></label><button className="button secondary" disabled={busy || !imageFile}>Добавить изображение</button>
        </form>
        <Link to={`/concert/${recordId}`} className="inline-button" onClick={close}>Посмотреть страницу концерта<Icon name="arrow" size={16} /></Link>
      </section>}
    </>}
  </Modal>;
}

function AdminContent({ notify }) {
  const [tab, setTab] = useState('concert');
  const [concerts, setConcerts] = useState([]), [venues, setVenues] = useState([]);
  const [loading, setLoading] = useState(true), [errors, setErrors] = useState({}), [revision, setRevision] = useState(0);
  const [editor, setEditor] = useState(null), [deleting, setDeleting] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const controllerRef = useRef(null);
  const closeEditor = useCallback(() => setEditor(null), []);
  const closeDelete = useCallback(() => { if (!busy) setDeleting(null); }, [busy]);
  const reload = useCallback(() => setRevision(value => value + 1), []);
  useEffect(() => {
    document.title = 'Редакция — Музыкальный понедельник';
    const controller = new AbortController(); controllerRef.current = controller;
    setLoading(true); setErrors({});
    Promise.allSettled([api.concerts(controller.signal), api.venues(controller.signal)]).then(results => {
      if (controller.signal.aborted) return;
      const nextErrors = {};
      for (const [index, kind] of ['concert', 'venue'].entries()) {
        if (results[index].status === 'fulfilled') (kind === 'concert' ? setConcerts : setVenues)(results[index].value);
        else nextErrors[kind] = results[index].reason.message;
      }
      setErrors(nextErrors); setLoading(false);
    });
    return () => controller.abort();
  }, [revision]);
  async function remove() {
    const signal = controllerRef.current.signal;
    setBusy(true); setError('');
    try {
      await (deleting.kind === 'concert' ? api.deleteConcert(deleting.id, signal) : api.deleteVenue(deleting.id, signal));
      if (!signal.aborted) { setDeleting(null); notify('Запись удалена.'); reload(); }
    } catch (error) { if (!signal.aborted) setError(error.message); }
    finally { if (!signal.aborted) setBusy(false); }
  }
  const items = tab === 'concert' ? concerts : venues;
  return <div className="container admin-page"><div className="section-heading"><div><div className="eyebrow">ЗА КУЛИСАМИ КЛУБА</div><h1>Редакция<span className="heading-dot">.</span></h1></div><p className="section-aside">Забота о каждой встрече</p></div>
    <div className="admin-toolbar"><div className="period-tabs" role="group" aria-label="Раздел редакции">{[['concert', 'Афиши'], ['venue', 'Площадки']].map(([value, label]) => <button key={value} aria-pressed={tab === value} className={tab === value ? 'selected' : ''} onClick={() => setTab(value)}>{label}</button>)}</div><button className="button" disabled={loading} onClick={() => setEditor({ kind: tab, id: null })}>{tab === 'concert' ? 'Новая афиша' : 'Новая площадка'}<Icon name="arrow" size={17} /></button></div>
    {loading ? <p className="admin-loading" role="status">Собираем афишу и площадки…</p> : errors[tab] ? <ErrorState message={errors[tab]} retry={reload} /> : !items.length ? <div className="empty-state"><Icon name="note" size={28} /><h3>{tab === 'concert' ? 'Время первой афиши.' : 'Найдём место для музыки.'}</h3><p>{tab === 'concert' ? 'Добавьте концерт — он появится в публичной афише.' : 'Добавьте площадку, чтобы привязать к ней концерт.'}</p></div> : <div className="admin-records">{items.map(item => <article key={item.id}><div><span className="eyebrow">{tab === 'concert' ? `${dateLong(item.starts_at)} · ${item.status === 'cancelled' ? 'ОТМЕНЁН' : 'ОПУБЛИКОВАН'}` : item.city}</span><h2>{item.title || item.name}</h2><p>{tab === 'concert' ? item.venue_names?.join(', ') : item.address}</p></div><div className="admin-record-actions">{tab === 'concert' && <Link to={`/concert/${item.id}`} className="inline-button">Открыть</Link>}<button className="inline-button" onClick={() => setEditor({ kind: tab, id: item.id })}>Редактировать</button><button className="inline-button danger-link" onClick={() => { setDeleting({ kind: tab, id: item.id, title: item.title || item.name }); setError(''); }}>Удалить</button></div></article>)}</div>}
    {editor && <Editor key={`${editor.kind}:${editor.id}`} {...editor} venues={venues} venuesError={errors.venue} reloadVenues={reload} onClose={closeEditor} onSaved={reload} notify={notify} />}
    {deleting && <Modal title={deleting.kind === 'concert' ? 'Удалить концерт?' : 'Удалить площадку?'} onClose={closeDelete}><p className="modal-intro"><strong>{deleting.title}</strong><br />{deleting.kind === 'concert' ? 'Вместе с афишей удалятся обсуждение, отзывы, изображения и связанные данные. Это действие нельзя отменить.' : 'Площадка исчезнет из списка мест проведения. Связанные концерты могут потребовать другой площадки.'}</p>{error && <p className="form-error" role="alert">{error}</p>}<div className="editor-actions"><button className="button" onClick={remove} disabled={busy}>{busy ? 'Удаляем…' : 'Подтвердить удаление'}</button><button className="inline-button" onClick={closeDelete} disabled={busy}>Отмена</button></div></Modal>}
  </div>;
}

export default function Admin({ session, restoring, notify }) {
  if (restoring) return <div className="container admin-loading" role="status">Проверяем доступ…</div>;
  if (session?.role !== 'admin') return <div className="container error-page"><ErrorState message="Этот раздел доступен только администратору клуба." /><Link to="/" className="inline-button">Вернуться к афише<Icon name="arrow" size={17} /></Link></div>;
  return <AdminContent notify={notify} />;
}
