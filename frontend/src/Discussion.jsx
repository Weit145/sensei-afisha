import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { api } from './api.js';
import { ErrorState, Icon } from './components.jsx';
import { dateLong, dateShort, hash, mergeMessages, participantName, time } from './utils.js';

export default function Discussion({ id, session, openAuth }) {
  const [messages, setMessages] = useState([]);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [sending, setSending] = useState(false);
  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [revision, setRevision] = useState(0);
  const initialized = useRef(false);
  const listRef = useRef(null);
  const scrollAction = useRef(null);
  const olderRequest = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    let timer;
    async function refresh() {
      if (olderRequest.current) { timer = setTimeout(refresh, 10000); return; }
      try {
        const result = await api.messages(id, { signal: controller.signal });
        if (controller.signal.aborted) return;
        const list = listRef.current;
        if (!initialized.current || !list || list.scrollHeight - list.scrollTop - list.clientHeight < 70) scrollAction.current = 'bottom';
        if (!initialized.current) {
          setCursor(result.next_cursor);
          setHasMore(result.has_more);
        }
        setMessages(previous => mergeMessages(previous, result.items));
        initialized.current = true;
        setError('');
      } catch (error) {
        if (!controller.signal.aborted) {
          if (!initialized.current) setError(error.message);
          else setActionError('Не удалось обновить обсуждение. Можно повторить по кнопке выше.');
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          timer = setTimeout(() => {
            if (!document.hidden) refresh();
            else timer = setTimeout(refresh, 15000);
          }, 10000);
        }
      }
    }
    setActionError('');
    refresh();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [id, revision]);

  useEffect(() => () => olderRequest.current?.abort(), []);

  useLayoutEffect(() => {
    const list = listRef.current;
    const action = scrollAction.current;
    if (!list || !action) return;
    if (action === 'bottom') list.scrollTop = list.scrollHeight;
    else list.scrollTop = action.top + list.scrollHeight - action.height;
    scrollAction.current = null;
  }, [messages]);

  async function loadOlder() {
    if (!cursor || olderRequest.current) return;
    const controller = new AbortController();
    olderRequest.current = controller;
    setLoadingOlder(true);
    setActionError('');
    try {
      const result = await api.messages(id, { before: cursor, signal: controller.signal });
      const list = listRef.current;
      if (list) scrollAction.current = { top: list.scrollTop, height: list.scrollHeight };
      setMessages(previous => mergeMessages(previous, result.items));
      setCursor(result.next_cursor);
      setHasMore(result.has_more);
    } catch (error) {
      if (!controller.signal.aborted) setActionError(error.message);
    } finally {
      olderRequest.current = null;
      if (!controller.signal.aborted) setLoadingOlder(false);
    }
  }

  async function send(event) {
    event.preventDefault();
    if (!session || !text.trim() || sending) return;
    setSending(true);
    setActionError('');
    try {
      const message = await api.sendMessage(id, text.trim(), session.token);
      scrollAction.current = 'bottom';
      setMessages(previous => mergeMessages(previous, [message]));
      setText('');
    } catch (error) { setActionError(error.message); }
    finally { setSending(false); }
  }

  return <section className="discussion-panel" aria-labelledby="discussion-heading" id="discussion">
    <div className="discussion-heading">
      <div><Icon name="chat" size={21} /><h2 id="discussion-heading">Обсуждение</h2></div>
      <button className="icon-button" onClick={() => setRevision(value => value + 1)} disabled={loading} aria-label="Обновить обсуждение"><Icon name="refresh" size={18} /></button>
    </div>
    <p className="discussion-subtitle">Договоритесь о встрече или обсудите программу.</p>
    <div className="messages-list" ref={listRef} role="log" aria-label="Сообщения обсуждения" aria-live="polite" aria-relevant="additions text" tabIndex={0}>
      {loading ? <p className="discussion-loading" role="status">Загружаем сообщения…</p>
        : error ? <ErrorState compact message={error} retry={() => setRevision(value => value + 1)} />
          : <>
            {hasMore && <button className="older-messages" onClick={loadOlder} disabled={loadingOlder}>{loadingOlder ? 'Загружаем историю…' : 'Более ранние сообщения'}</button>}
            {!messages.length && <div className="conversation-empty"><Icon name="chat" size={38} /><h3>Кто идёт на концерт?</h3><p>Начните разговор и найдите компанию.</p></div>}
            {messages.map((message, index) => {
              const own = message.author_id === session?.id;
              const dayChanged = index === 0 || dateLong(message.created_at) !== dateLong(messages[index - 1].created_at);
              return <div key={message.id}>
                {dayChanged && <div className="chat-date">{dateShort(message.created_at)}</div>}
                <article className={`message ${own ? 'own-message' : ''}`}>
                  <span className={`avatar avatar-${hash(message.author_id) % 4}`} aria-hidden="true">{own ? 'ВЫ' : message.author_id.slice(0, 2).toUpperCase()}</span>
                  <div className="message-body"><div className="message-meta"><strong>{own ? 'Вы' : participantName(message.author_id)}</strong><time dateTime={message.created_at}>{time(message.created_at)}</time></div><p>{message.text}</p></div>
                </article>
              </div>;
            })}
          </>}
    </div>
    <form className="message-form" onSubmit={send}>
      {actionError && <p className="form-error" role="alert">{actionError}</p>}
      <label className="sr-only" htmlFor="new-message">Новое сообщение</label>
      <textarea id="new-message" value={text} onChange={event => setText(event.target.value)} placeholder={session ? 'Напишите сообщение…' : 'Войдите, чтобы написать сообщение'} rows={3} maxLength={2000} disabled={!session || sending} onKeyDown={event => {
        if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) { event.preventDefault(); event.currentTarget.form.requestSubmit(); }
      }} />
      <div className="message-form-bottom">
        {session ? <><span>{text.length}/2000</span><button className="button" disabled={!text.trim() || sending}>{sending ? 'Отправляем…' : 'Отправить'}<Icon name="send" size={16} /></button></>
          : <><span>Общение с участниками клуба</span><button type="button" className="button" onClick={openAuth}>Войти<Icon name="arrow" size={16} /></button></>}
      </div>
    </form>
  </section>;
}
