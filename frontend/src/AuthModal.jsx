import { useCallback, useState } from 'react';
import { api, DEMO } from './api.js';
import { Icon, Modal } from './components.jsx';

export default function AuthModal({ onClose, onConnect }) {
  const [tab, setTab] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const close = useCallback(() => { if (!busy) onClose(); }, [busy, onClose]);

  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    try {
      const user = await api[tab === 'join' ? 'register' : 'login'](username.trim(), password);
      setPassword(''); onConnect(user); onClose();
    } catch (error) { setError(error.message); }
    finally { setBusy(false); }
  }

  if (DEMO) return <Modal title="Знакомьтесь с клубом." onClose={close}><p className="modal-intro">Сейчас открыт режим просмотра. Вход и публикации доступны при запуске с подключённым сервером.</p><button className="button" onClick={close}>Продолжить знакомство<Icon name="arrow" /></button></Modal>;
  return <Modal title={tab === 'join' ? 'Хорошая музыка объединяет.' : 'Рады новой встрече.'} onClose={close}>
    <p className="modal-intro">Войдите, чтобы общаться и делиться впечатлениями. После регистрации вы сразу станете участником клуба.</p>
    <div className="auth-tabs" role="group" aria-label="Вход или регистрация">
      <button aria-pressed={tab === 'login'} className={tab === 'login' ? 'selected' : ''} onClick={() => { setTab('login'); setError(''); }} disabled={busy}>Войти</button>
      <button aria-pressed={tab === 'join'} className={tab === 'join' ? 'selected' : ''} onClick={() => { setTab('join'); setError(''); }} disabled={busy}>Регистрация</button>
    </div>
    <form onSubmit={submit} className="form-stack" aria-busy={busy}>
      <label>Имя пользователя<input name="username" value={username} onChange={event => setUsername(event.target.value)} autoComplete="username" required minLength={tab === 'join' ? 3 : 1} maxLength={30} pattern={tab === 'join' ? '[a-zA-Z0-9_]+' : undefined} disabled={busy} aria-describedby={tab === 'join' ? 'username-hint' : undefined} /></label>
      {tab === 'join' && <small id="username-hint">От 3 до 30 символов: латинские буквы, цифры и знак подчёркивания.</small>}
      <label>Пароль<input name="password" type="password" value={password} onChange={event => setPassword(event.target.value)} autoComplete={tab === 'join' ? 'new-password' : 'current-password'} required minLength={tab === 'join' ? 8 : 1} maxLength={128} disabled={busy} /></label>
      {tab === 'join' && <small>От 8 до 128 символов.</small>}
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="button" disabled={busy}>{busy ? 'Входим в клуб…' : tab === 'join' ? 'Зарегистрироваться' : 'Войти'}<Icon name="arrow" size={17} /></button>
      <p className="form-note">Пароль не сохраняется в хранилище сайта. Сессия восстанавливается через защищённую cookie.</p>
    </form>
  </Modal>;
}
