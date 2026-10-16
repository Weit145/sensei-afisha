import { useCallback, useState } from 'react';
import { api, DEMO } from './api.js';
import { Icon, Modal } from './components.jsx';
import { parseAccessKey } from './utils.js';

export default function AuthModal({ onClose, onConnect }) {
  const [tab, setTab] = useState('join');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [created, setCreated] = useState(false);
  const close = useCallback(() => { if (!busy) onClose(); }, [busy, onClose]);

  async function register(event) {
    event.preventDefault();
    setError(''); setBusy(true);
    try { await api.register(username.trim(), password); setCreated(true); setPassword(''); }
    catch (error) { setError(error.message); }
    finally { setBusy(false); }
  }

  function connect(event) {
    event.preventDefault();
    const session = parseAccessKey(token);
    if (!session) { setError('Проверьте ключ: он должен быть действующим и принадлежать участнику клуба.'); return; }
    onConnect(session); onClose();
  }

  if (DEMO) return <Modal title="Знакомьтесь с клубом." onClose={close}><p className="modal-intro">Сейчас открыт режим просмотра с демонстрационными концертами. Регистрация и отправка сообщений доступны при обычном запуске с подключённым сервером.</p><button className="button" onClick={close}>Продолжить знакомство<Icon name="arrow" /></button></Modal>;

  return <Modal title={created ? 'Вы в списке гостей.' : 'Хорошая музыка объединяет.'} onClose={close}>
    {created ? <div className="registration-success"><span className="empty-icon"><Icon name="check" size={30} /></span><p>Аккаунт <strong>{username.trim().toLowerCase()}</strong> создан.</p><p className="muted">Вход по паролю пока недоступен. Если организаторы выдали вам ключ доступа, его можно подключить во вкладке «Войти».</p><button className="button" onClick={() => { setCreated(false); setTab('login'); }}>Ко входу<Icon name="arrow" /></button></div> : <>
      <p className="modal-intro">Сохраняйте встречи с музыкой и продолжайте разговор после последнего аккорда.</p>
      <div className="auth-tabs" role="tablist" aria-label="Способ подключения">
        <button role="tab" aria-selected={tab === 'join'} onClick={() => { setTab('join'); setError(''); }} disabled={busy}>Регистрация</button>
        <button role="tab" aria-selected={tab === 'login'} onClick={() => { setTab('login'); setError(''); }} disabled={busy}>Войти</button>
      </div>
      {tab === 'join' ? <form onSubmit={register} className="form-stack">
        <label>Имя пользователя<input value={username} onChange={event => setUsername(event.target.value)} placeholder="Например, music_lover" autoComplete="username" required minLength={3} maxLength={30} pattern="[A-Za-z0-9_]+" disabled={busy} aria-describedby="username-hint" /></label>
        <small id="username-hint">От 3 до 30 символов: латинские буквы, цифры и _</small>
        <label>Пароль<input type="password" value={password} onChange={event => setPassword(event.target.value)} autoComplete="new-password" placeholder="Не меньше 8 символов" minLength={8} maxLength={128} required disabled={busy} /></label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="button full" disabled={busy}>{busy ? 'Создаём аккаунт…' : 'Присоединиться к клубу'}<Icon name="arrow" /></button>
        <p className="form-note">Регистрация создаёт аккаунт. Вход по паролю ещё не подключён.</p>
      </form> : <form onSubmit={connect} className="form-stack">
        <div className="notice">Вход по паролю пока недоступен. Для обсуждений можно использовать ключ доступа, полученный у организаторов.</div>
        <label>Ключ доступа<textarea value={token} onChange={event => setToken(event.target.value)} placeholder="Вставьте ваш ключ" rows={4} required autoComplete="off" spellCheck={false} /></label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="button full">Подключиться<Icon name="arrow" /></button>
        <p className="form-note">Ключ хранится до закрытия вкладки. Сервер проверяет его при отправке сообщения.</p>
      </form>}
    </>}
  </Modal>;
}
