import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { api, connectDiscussion, DEMO } from './api.js';
import { ErrorState, Icon } from './components.jsx';
import { dateLong, dateShort, hash, initials, mergeMessages, participantName, time } from './utils.js';

export default function Discussion({ id, session, openAuth }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [sending, setSending] = useState(false);
  const [text, setText] = useState('');
  const [cursor, setCursor] = useState(null);
  const [olderBusy, setOlderBusy] = useState(false);
  const [connection, setConnection] = useState(DEMO ? 'demo' : 'connecting');
  const [revision, setRevision] = useState(0);
  const listRef = useRef(null), messagesRef = useRef([]), snapshot = useRef(null), loadRef = useRef(null), controllerRef = useRef(null);
  const initialized = useRef(false);
  useEffect(() => { setText(''); setActionError(''); }, [session?.id]);

  function remember(kind = 'latest') {
    const list = listRef.current;
    if (list) snapshot.current = { kind, height: list.scrollHeight, top: list.scrollTop, bottom: !initialized.current || list.scrollHeight - list.scrollTop - list.clientHeight < 70 };
  }
  function merge(incoming, kind) {
    remember(kind);
    const next = mergeMessages(messagesRef.current, incoming);
    messagesRef.current = next; setMessages(next);
  }
  useLayoutEffect(() => {
    const list = listRef.current, saved = snapshot.current;
    if (!list || !saved) return;
    if (saved.kind === 'older') list.scrollTop = saved.top + list.scrollHeight - saved.height;
    else if (saved.kind === 'sent' || saved.bottom) list.scrollTop = list.scrollHeight;
    snapshot.current = null;
  }, [messages, loading, olderBusy]);

  useEffect(() => {
    const controller = new AbortController(); controllerRef.current = controller;
    let pending = false, busy = false;
    async function load() {
      if (busy) { pending = true; return; }
      busy = true; setUpdating(true);
      try {
        do {
          pending = false;
          const known = new Set(messagesRef.current.map(item => item.id));
          const result = await api.messages(id, { signal: controller.signal });
          const incoming = [...result.items];
          let page = result;
          // Catch up through every missed page after a long disconnection.
          while (known.size && page.has_more && page.next_cursor && !page.items.some(item => known.has(item.id))) {
            page = await api.messages(id, { before: page.next_cursor, signal: controller.signal });
            incoming.push(...page.items);
          }
          if (controller.signal.aborted) return;
          if (!initialized.current) setCursor(page.has_more ? page.next_cursor : null);
          merge(incoming, 'latest'); initialized.current = true;
          setError(''); setActionError(''); setLoading(false);
        } while (pending && !controller.signal.aborted);
      } catch (error) {
        if (!controller.signal.aborted) {
          if (!initialized.current) setError(error.message);
          else setActionError(error.message);
        }
      } finally { busy = false; if (!controller.signal.aborted) { setUpdating(false); setLoading(false); } }
    }
    loadRef.current = load;
    load();
    const close = connectDiscussion(id, { onUpdate: load, onStatus: setConnection });
    return () => { controller.abort(); close(); loadRef.current = null; };
  }, [id, revision]);

  async function earlier() {
    if (!cursor || olderBusy) return;
    const signal = controllerRef.current.signal;
    setOlderBusy(true); setActionError('');
    try {
      const result = await api.messages(id, { before: cursor, signal });
      if (signal.aborted) return;
      merge(result.items, 'older'); setCursor(result.has_more ? result.next_cursor : null);
    } catch (error) { if (!signal.aborted) setActionError(error.message); }
    finally { if (!signal.aborted) setOlderBusy(false); }
  }
  async function send(event) {
    event.preventDefault();
    if (!session || !text.trim() || sending) return;
    const signal = controllerRef.current.signal;
    setSending(true); setActionError('');
    try {
      const message = await api.sendMessage(id, text.trim(), signal);
      if (!signal.aborted) { merge([message], 'sent'); setText(''); }
    } catch (error) { if (!signal.aborted) setActionError(error.message); }
    finally { if (!signal.aborted) setSending(false); }
  }
  const refresh = () => {
    if (connection === 'offline') setRevision(value => value + 1);
    else loadRef.current?.();
  };

  return <section className="discussion-panel" aria-labelledby="discussion-heading" id="discussion" tabIndex={-1}>
    <div className="discussion-heading"><div><Icon name="chat" size={22} /><h2 id="discussion-heading">Обсуждение</h2>{!loading && <span className="message-count">{messages.length}</span>}</div><button className="icon-button" onClick={refresh} disabled={updating || sending || olderBusy} aria-label="Обновить обсуждение" title="Обновить"><Icon name="refresh" size={17} /></button></div>
    <p className="discussion-subtitle">Предложите встретиться перед концертом — компания найдётся в разговоре.</p>
    <p className={`connection-status ${connection === 'connected' ? 'live' : ''}`} role="status">{connection === 'connected' ? 'Разговор обновляется автоматически' : connection === 'demo' ? 'Демонстрационное обсуждение' : connection === 'connecting' ? 'Подключаем обновления…' : connection === 'reconnecting' ? 'Восстанавливаем соединение… Можно обновить вручную.' : 'Автообновление приостановлено. Нажмите «Обновить обсуждение».'}</p>
    <div className="messages-list" ref={listRef} role="log" aria-label="Сообщения обсуждения" aria-live="polite" aria-relevant="additions" tabIndex={0}>
      {loading ? <p className="discussion-loading" role="status">Загружаем разговор…</p> : error ? <ErrorState compact message={error} retry={refresh} /> : <>
        {cursor && <button className="earlier-button inline-button" onClick={earlier} disabled={olderBusy || sending}>{olderBusy ? 'Загружаем…' : 'Показать более ранние'}</button>}
        {!messages.length ? <div className="conversation-empty"><span className="conversation-drawing" aria-hidden="true"><Icon name="chat" size={44} /><span>♪</span></span><h3>Займите первое кресло.</h3><p>Самое время познакомиться<br />и договориться о встрече.</p></div> : messages.map((message, index) => {
          const own = message.author_id === session?.id;
          const name = own ? 'Вы' : participantName(message.author_id);
          const dayChanged = index === 0 || dateLong(message.created_at) !== dateLong(messages[index - 1].created_at);
          return <div key={message.id}>{dayChanged && <div className="chat-date">{dateShort(message.created_at)}</div>}<article className={`message ${own ? 'own-message' : ''}`}><span className={`avatar avatar-${hash(message.author_id) % 4}`} aria-hidden="true">{own ? 'ВЫ' : initials(name.split(' ')[1])}</span><div className="message-body"><div className="message-meta"><strong>{name}</strong><time dateTime={message.created_at}>{time(message.created_at)}</time></div><p>{message.text}</p></div></article></div>;
        })}
      </>}
    </div>
    <form className="message-form" onSubmit={send} aria-busy={sending}>
      {actionError && <p className="form-error" role="alert">{actionError} <button type="button" className="inline-button" onClick={refresh} disabled={updating}>Обновить историю</button></p>}
      <label className="sr-only" htmlFor="new-message">Новое сообщение</label><textarea id="new-message" value={text} onChange={event => setText(event.target.value)} placeholder={session ? 'О чём хочется поговорить?' : 'Присоединитесь к разговору…'} rows={3} maxLength={2000} disabled={!session || sending} onKeyDown={event => { if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) { event.preventDefault(); event.currentTarget.form.requestSubmit(); } }} />
      <div className="message-form-bottom">{session ? <><span>{text.length}/2000 · Ctrl / ⌘ + Enter</span><button className="button" disabled={!text.trim() || sending}>{sending ? 'Отправляем…' : 'Отправить'}<Icon name="send" size={16} /></button></> : <><span>Для сообщений нужен вход в клуб</span><button type="button" className="button" onClick={openAuth}>Войти<Icon name="arrow" size={16} /></button></>}</div>
    </form>
  </section>;
}
