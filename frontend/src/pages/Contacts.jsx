import { useEffect, useRef, useState } from 'react';
import { api } from '../api.js';
import { ErrorState, Icon } from '../components.jsx';
import { contactsPayload } from '../contactsUtils.js';

function ContactsForm({ session }) {
  const [form, setForm] = useState({ tg_url: '', vk_url: '' });
  const [loading, setLoading] = useState(true), [saving, setSaving] = useState(false);
  const [error, setError] = useState(''), [fields, setFields] = useState({}), [status, setStatus] = useState('');
  const [revision, setRevision] = useState(0);
  const [ready, setReady] = useState(false);
  const controllerRef = useRef(null);
  const saveRef = useRef(null), wasSaving = useRef(false);
  useEffect(() => {
    if (!saving && wasSaving.current && document.activeElement === document.body) saveRef.current?.focus();
    wasSaving.current = saving;
  }, [saving]);
  useEffect(() => {
    const controller = new AbortController(); controllerRef.current = controller;
    setLoading(true); setReady(false); setError('');
    api.myContacts(controller.signal).then(result => {
      if (!controller.signal.aborted) { setForm({ tg_url: result.tg_url || '', vk_url: result.vk_url || '' }); setReady(true); }
    }).catch(error => { if (!controller.signal.aborted) setError(error.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [revision]);

  function change(field, value) {
    setForm(old => ({ ...old, [field]: value })); setFields(old => ({ ...old, [field]: '' })); setStatus(''); setError('');
  }
  async function save(event) {
    event.preventDefault(); setError(''); setStatus('');
    const { body, errors } = contactsPayload(form); setFields(errors);
    if (Object.keys(errors).length) { event.currentTarget.querySelector(`[name="${Object.keys(errors)[0]}"]`)?.focus(); return; }
    const signal = controllerRef.current.signal;
    setSaving(true);
    try {
      const result = await api.updateContacts(body, signal);
      if (!signal.aborted) { setForm({ tg_url: result.tg_url || '', vk_url: result.vk_url || '' }); setStatus('Контакты сохранены. Участники клуба увидят только указанные ссылки.'); }
    } catch (error) { if (!signal.aborted) { setError(error.message); setFields(error.fields || {}); } }
    finally { if (!signal.aborted) setSaving(false); }
  }

  if (loading) return <p className="contacts-loading" role="status">Загружаем ваши контакты…</p>;
  if (!ready) return <ErrorState message={error} retry={() => setRevision(value => value + 1)} />;
  return <section className="contacts-sheet" aria-labelledby="contacts-form-title">
    <h2 id="contacts-form-title">Как с вами связаться, {session.username}?</h2>
    <p className="contacts-intro">Ссылки на Telegram и ВКонтакте будут доступны другим авторизованным участникам клуба. Оба поля необязательны.</p>
    <form className="form-stack" onSubmit={save} aria-busy={saving} noValidate>
      {['tg_url', 'vk_url'].map(field => <div className="contact-field" key={field}>
        <label htmlFor={field}>{field === 'tg_url' ? 'Telegram' : 'ВКонтакте'}</label>
        <div className="contact-input-row"><input id={field} name={field} type="url" inputMode="url" autoComplete="off" maxLength={255} value={form[field]} placeholder={field === 'tg_url' ? 'https://t.me/username' : 'https://vk.com/username'} disabled={saving} onChange={event => change(field, event.target.value)} aria-invalid={Boolean(fields[field])} aria-describedby={`${field}-hint${fields[field] ? ` ${field}-error` : ''}`} /><button type="button" className="inline-button" disabled={saving || !form[field]} onClick={() => change(field, '')} aria-label={`Очистить ${field === 'tg_url' ? 'Telegram' : 'ВКонтакте'}`}>Убрать</button></div>
        <small id={`${field}-hint`}>{field === 'tg_url' ? 'HTTPS-ссылка на t.me или telegram.me.' : 'HTTPS-ссылка на vk.com.'}</small>
        {fields[field] && <p id={`${field}-error`} className="form-error" role="alert">{fields[field]}</p>}
      </div>)}
      <p className="small-text muted">Чтобы удалить контакт, очистите поле и сохраните изменения.</p>
      {error && <p className="form-error" role="alert">{error} <button type="button" className="inline-button" onClick={() => setRevision(value => value + 1)} disabled={saving}>Загрузить заново</button></p>}
      <p className="contact-success" role="status">{status}</p>
      <button ref={saveRef} className="button" disabled={saving}>{saving ? 'Сохраняем…' : 'Сохранить контакты'}<Icon name="check" size={17} /></button>
    </form>
  </section>;
}

export default function Contacts({ session, restoring, openAuth }) {
  useEffect(() => { document.title = 'Мои контакты — Музыкальный понедельник'; }, []);
  return <div className="container contacts-page"><div className="section-heading"><div><div className="eyebrow">ПРОДОЛЖИТЬ РАЗГОВОР</div><h1>Мои контакты<span className="heading-dot">.</span></h1></div><p className="section-aside">Знакомства после последнего аккорда</p></div>
    {restoring ? <p role="status">Проверяем вход…</p> : session ? <ContactsForm key={session.id} session={session} /> : <div className="contacts-sheet"><h2>Для контактов нужен вход в клуб.</h2><p className="contacts-intro">Если сессия истекла, войдите снова. Ваши сохранённые ссылки останутся в профиле.</p><button className="button" onClick={openAuth}>Войти в клуб<Icon name="arrow" /></button></div>}
  </div>;
}
