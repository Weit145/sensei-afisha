import { useEffect, useState } from 'react';
import { api } from './api.js';
import { Icon, Modal } from './components.jsx';
import { contactValue } from './contactsUtils.js';

export default function ContactCard({ userId, session, openAuth, onClose }) {
  const [data, setData] = useState(null), [loading, setLoading] = useState(true), [error, setError] = useState(null), [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError(null);
    if (!session) { setLoading(false); return () => controller.abort(); }
    setLoading(true);
    api.userContacts(userId, controller.signal).then(result => { if (!controller.signal.aborted) setData(result); }).catch(error => { if (!controller.signal.aborted) setError(error); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [userId, session?.id, revision]);
  const login = () => { onClose(); openAuth(); };
  const discuss = () => { onClose(); requestAnimationFrame(() => { document.getElementById('discussion')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); document.getElementById('new-message')?.focus(); }); };
  const links = [];
  if (session && data) for (const [field, label] of [['tg_url', 'Telegram'], ['vk_url', 'ВКонтакте']]) {
    try { const href = contactValue(data[field], field); if (href) links.push({ field, label, href }); } catch { /* Never render an unsafe URL, even from an unexpected server response. */ }
  }
  return <Modal title={session && data ? data.nickname : 'Связаться со слушателем'} onClose={onClose} className="contact-card">
    {!session || error?.status === 401 ? <><p className="modal-intro">Контакты доступны участникам клуба после входа. Если сессия истекла, войдите снова.</p><button className="button" onClick={login}>Войти в клуб<Icon name="arrow" /></button></> : loading ? <p className="modal-intro" role="status">Загружаем карточку участника…</p> : error ? <><p className="form-error contact-card-error" role="alert">{error.status === 404 ? 'Пользователь не найден. Возможно, его аккаунт удалён.' : error.message}</p><div className="editor-actions"><button className="button secondary" onClick={() => setRevision(value => value + 1)}>Попробовать ещё раз<Icon name="refresh" size={17} /></button><button className="inline-button" onClick={discuss}>Вернуться в обсуждение</button></div></> : <>
      <p className="modal-intro">{links.length ? 'Продолжите разговор удобным способом.' : 'Участник пока не указал контакты. Предложите пообщаться в обсуждении концерта.'}</p>
      <div className="contact-links">{links.map(link => <a className="button secondary" href={link.href} target="_blank" rel="noopener noreferrer" key={link.field}>{link.label}<Icon name="external" size={17} /></a>)}</div>
      <button className="inline-button" onClick={discuss}>Написать в обсуждении<Icon name="chat" size={16} /></button>
    </>}
  </Modal>;
}
