import { StrictMode, useCallback, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import AuthModal from './AuthModal.jsx';
import Home from './pages/Home.jsx';
import Concert from './pages/Concert.jsx';
import Club from './pages/Club.jsx';
import Admin from './pages/Admin.jsx';
import Contacts from './pages/Contacts.jsx';
import { Icon, Link } from './components.jsx';
import { readStored, writeStored } from './utils.js';
import { api, DEMO } from './api.js';
import './styles.css';

const PLANS_KEY = 'musical-monday:plans:v1';

function App() {
  const [path, setPath] = useState(location.pathname);
  const [showAuth, setShowAuth] = useState(false);
  const [session, setSession] = useState(api.getSession);
  const [restoring, setRestoring] = useState(true);
  const [authError, setAuthError] = useState('');
  const [loggingOut, setLoggingOut] = useState(false);
  const [plans, setPlans] = useState(() => {
    const saved = readStored(PLANS_KEY, []);
    return Array.isArray(saved) ? saved.filter(id => typeof id === 'string') : [];
  });
  const [toast, setToast] = useState('');
  const notify = useCallback(message => setToast(message), []);
  const openAuth = useCallback(() => setShowAuth(true), []);
  const closeAuth = useCallback(() => setShowAuth(false), []);
  const connect = useCallback(value => {
    setAuthError(''); notify(`Вы в клубе, ${value.username}.`);
  }, [notify]);

  const restore = useCallback(async () => {
    setRestoring(true); setAuthError('');
    try { await api.restoreSession(); }
    catch (error) { setAuthError(error.message); }
    finally { setRestoring(false); }
  }, []);
  useEffect(() => {
    // Remove legacy pasted keys left by older versions of the frontend.
    try { sessionStorage.removeItem('musical-monday:session:v1'); } catch { /* Storage can be unavailable. */ }
    const unsubscribe = api.subscribe(setSession);
    restore();
    return unsubscribe;
  }, [restore]);

  async function disconnect() {
    setLoggingOut(true); setAuthError('');
    try { await api.logout(); notify('Вы вышли из клуба.'); }
    catch (error) { setAuthError(`Выход не завершён. ${error.message}`); }
    finally { setLoggingOut(false); }
  }

  useEffect(() => {
    const navigate = () => setPath(location.pathname);
    const expired = () => notify('Сессия истекла. Войдите в клуб снова.');
    window.addEventListener('popstate', navigate);
    window.addEventListener('session-expired', expired);
    return () => { window.removeEventListener('popstate', navigate); window.removeEventListener('session-expired', expired); };
  }, [notify]);
  useEffect(() => { if (!toast) return; const timer = setTimeout(() => setToast(''), 5500); return () => clearTimeout(timer); }, [toast]);
  useEffect(() => {
    const sync = event => { if (event.key === PLANS_KEY) { const value = readStored(PLANS_KEY, []); if (Array.isArray(value)) setPlans(value.filter(id => typeof id === 'string')); } };
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);

  function togglePlan(id) {
    const next = plans.includes(id) ? plans.filter(value => value !== id) : [...plans, id];
    const saved = writeStored(PLANS_KEY, next);
    setPlans(next);
    notify(saved ? next.includes(id) ? 'Концерт в ваших планах. Сохранено только в этом браузере.' : 'Концерт убран из ваших планов.' : 'Хранилище браузера недоступно. План сохранён до обновления страницы.');
  }

  const detail = path.match(/^\/concert\/([^/]+)\/?$/);
  const common = { plans, togglePlan, session, openAuth, notify };
  return <>
    <a className="skip-link" href="#main">Перейти к содержанию</a>
    {DEMO && <div className="demo-banner" role="status">Режим просмотра <span>· Демонстрационные концерты. Отправка сообщений и регистрация отключены.</span></div>}
    <header className="site-header"><div className="header-inner">
      <Link to="/" className="brand" aria-label="Музыкальный понедельник — на главную"><span className="brand-mark">м<span>п</span><i /></span><span>музыкальный<br />понедельник</span></Link>
      <nav aria-label="Основная навигация"><Link to="/" className={path === '/' || detail ? 'active' : ''}>Афиша</Link><Link to="/plans" className={path === '/plans' ? 'active' : ''}>Мои планы{plans.length > 0 && <span className="nav-count">{plans.length}</span>}</Link><Link to="/club" className={path === '/club' ? 'active' : ''}>О клубе</Link>{session && <Link to="/contacts" className={path === '/contacts' ? 'active' : ''}>Мои контакты</Link>}{session?.role === 'admin' && <Link to="/admin" className={path === '/admin' ? 'active' : ''}>Редакция</Link>}</nav>
      {session ? <button className="login-button" onClick={disconnect} disabled={loggingOut}><Icon name="logout" size={17} /><span>{loggingOut ? 'Выходим…' : `Выйти · ${session.username}`}</span></button> : <button className="login-button" onClick={openAuth} disabled={restoring}><Icon name="user" size={17} /><span>{restoring ? 'Проверяем вход…' : 'Войти в клуб'}</span><Icon name="arrow" size={17} /></button>}
    </div></header>
    {authError && <div className="session-notice container" role="alert"><span>{authError}</span><button className="inline-button" disabled={restoring || loggingOut} onClick={session ? disconnect : restore}>Повторить</button></div>}
    <main id="main" tabIndex={-1}>
      {detail ? <Concert key={detail[1]} id={detail[1]} {...common} /> : path === '/' || path === '/plans' ? <Home key={path} onlyPlans={path === '/plans'} {...common} /> : path === '/club' ? <Club openAuth={openAuth} session={session} /> : path === '/contacts' ? <Contacts session={session} restoring={restoring} openAuth={openAuth} /> : path === '/admin' ? <Admin session={session} restoring={restoring} notify={notify} /> : <div className="not-found container"><span className="eyebrow">404 · ПАУЗА МЕЖДУ ЧАСТЯМИ</span><h1>Кажется, здесь тишина.</h1><p>Такой страницы нет. Но в афише наверняка найдётся что послушать.</p><Link to="/" className="button">Вернуться к афише<Icon name="arrow" /></Link></div>}
    </main>
    <footer className="site-footer container"><Link to="/" className="footer-name">Музыкальный понедельник<span>Клуб слушателей</span></Link><p>Музыка заканчивается.<br />Разговор продолжается.</p><Link to="/club">О нашем клубе<Icon name="arrow" size={16} /></Link><span className="footer-year">{new Date().getFullYear()}</span></footer>
    {showAuth && <AuthModal onClose={closeAuth} onConnect={connect} />}
    {toast && <div className="toast" role="status"><Icon name="note" size={18} /><span>{toast}</span><button aria-label="Закрыть уведомление" onClick={() => setToast('')}><Icon name="close" size={16} /></button></div>}
  </>;
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>);
