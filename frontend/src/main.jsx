import { StrictMode, useCallback, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import AuthModal from './AuthModal.jsx';
import Home from './pages/Home.jsx';
import Concert from './pages/Concert.jsx';
import Club from './pages/Club.jsx';
import { Icon, Link } from './components.jsx';
import { parseAccessKey, readStored, writeStored } from './utils.js';
import { DEMO } from './api.js';
import './styles.css';

const PLANS_KEY = 'musical-monday:plans:v1';
const SESSION_KEY = 'musical-monday:session:v1';

function App() {
  const [path, setPath] = useState(location.pathname);
  const [showAuth, setShowAuth] = useState(false);
  const [session, setSession] = useState(() => {
    const saved = readStored(SESSION_KEY, null, 'sessionStorage');
    return saved?.token ? parseAccessKey(saved.token) : null;
  });
  const [plans, setPlans] = useState(() => {
    const saved = readStored(PLANS_KEY, []);
    return Array.isArray(saved) ? saved.filter(id => typeof id === 'string') : [];
  });
  const [toast, setToast] = useState('');
  const notify = useCallback(message => setToast(message), []);
  const openAuth = useCallback(() => setShowAuth(true), []);
  const closeAuth = useCallback(() => setShowAuth(false), []);
  const connect = useCallback(value => {
    if (!writeStored(SESSION_KEY, value, 'sessionStorage')) notify('Ключ подключён только до обновления страницы: хранилище браузера недоступно.');
    else notify('Ключ доступа подключён. Теперь можно отправить сообщение.');
    setSession(value);
  }, [notify]);
  const disconnect = useCallback(() => { setSession(null); writeStored(SESSION_KEY, null, 'sessionStorage'); }, []);

  useEffect(() => {
    const navigate = () => setPath(location.pathname);
    const expired = () => { disconnect(); notify('Срок действия ключа истёк. Подключитесь заново, чтобы отправлять сообщения.'); };
    window.addEventListener('popstate', navigate);
    window.addEventListener('session-expired', expired);
    return () => { window.removeEventListener('popstate', navigate); window.removeEventListener('session-expired', expired); };
  }, [disconnect, notify]);
  useEffect(() => {
    if (!session) return;
    const timer = setTimeout(() => { disconnect(); notify('Срок действия ключа истёк.'); }, Math.min(session.expiresAt - Date.now(), 2147483647));
    return () => clearTimeout(timer);
  }, [session, disconnect, notify]);
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
    notify(saved ? next.includes(id) ? 'Концерт в ваших планах. Сохранено на этом устройстве.' : 'Концерт убран из ваших планов.' : 'Хранилище браузера недоступно. План сохранён до обновления страницы.');
  }

  const detail = path.match(/^\/concert\/([^/]+)\/?$/);
  const common = { plans, togglePlan, session, openAuth, notify };
  return <>
    <a className="skip-link" href="#main">Перейти к содержанию</a>
    {DEMO && <div className="demo-banner" role="status">Режим просмотра <span>· Демонстрационные концерты. Отправка сообщений и регистрация отключены.</span></div>}
    <header className="site-header"><div className="header-inner">
      <Link to="/" className="brand" aria-label="Музыкальный понедельник — на главную"><span className="brand-mark">м<span>п</span><i /></span><span>музыкальный<br />понедельник</span></Link>
      <nav aria-label="Основная навигация"><Link to="/" className={path === '/' || detail ? 'active' : ''}>Афиша</Link><Link to="/plans" className={path === '/plans' ? 'active' : ''}>Мои планы{plans.length > 0 && <span className="nav-count">{plans.length}</span>}</Link><Link to="/club" className={path === '/club' ? 'active' : ''}>О клубе</Link></nav>
      {session ? <button className="login-button" onClick={() => { disconnect(); notify('Вы вышли из клуба.'); }}><Icon name="logout" size={17} /><span>Выйти</span></button> : <button className="login-button" onClick={openAuth}><Icon name="user" size={17} /><span>Войти в клуб</span><Icon name="arrow" size={17} /></button>}
    </div></header>
    <main id="main" tabIndex={-1}>
      {detail ? <Concert key={detail[1]} id={detail[1]} {...common} /> : path === '/' || path === '/plans' ? <Home key={path} onlyPlans={path === '/plans'} {...common} /> : path === '/club' ? <Club openAuth={openAuth} /> : <div className="not-found container"><span className="eyebrow">404 · ПАУЗА МЕЖДУ ЧАСТЯМИ</span><h1>Кажется, здесь тишина.</h1><p>Такой страницы нет. Но в афише наверняка найдётся что послушать.</p><Link to="/" className="button">Вернуться к афише<Icon name="arrow" /></Link></div>}
    </main>
    <footer className="site-footer container"><Link to="/" className="footer-name">Музыкальный понедельник<span>Клуб слушателей</span></Link><p>Музыка заканчивается.<br />Разговор продолжается.</p><Link to="/club">О нашем клубе<Icon name="arrow" size={16} /></Link><span className="footer-year">{new Date().getFullYear()}</span></footer>
    {showAuth && <AuthModal onClose={closeAuth} onConnect={connect} />}
    {toast && <div className="toast" role="status"><Icon name="note" size={18} /><span>{toast}</span><button aria-label="Закрыть уведомление" onClick={() => setToast('')}><Icon name="close" size={16} /></button></div>}
  </>;
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>);
