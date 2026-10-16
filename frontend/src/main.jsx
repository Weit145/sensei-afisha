import { StrictMode, useCallback, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import AuthModal from './AuthModal.jsx';
import Home from './pages/Home.jsx';
import Concert from './pages/Concert.jsx';
import { Icon, Link } from './components.jsx';
import { parseAccessKey, readStored, writeStored } from './utils.js';
import './styles.css';

const SESSION_KEY = 'musical-monday:session:v1';

function App() {
  const [path, setPath] = useState(location.pathname);
  const [showAuth, setShowAuth] = useState(false);
  const [session, setSession] = useState(() => {
    const saved = readStored(SESSION_KEY, null, 'sessionStorage');
    return saved?.token ? parseAccessKey(saved.token) : null;
  });
  const [toast, setToast] = useState('');
  const notify = useCallback(message => setToast(message), []);
  const openAuth = useCallback(() => setShowAuth(true), []);
  const closeAuth = useCallback(() => setShowAuth(false), []);
  const disconnect = useCallback(() => {
    setSession(null);
    writeStored(SESSION_KEY, null, 'sessionStorage');
  }, []);
  const connect = useCallback(value => {
    const stored = writeStored(SESSION_KEY, value, 'sessionStorage');
    setSession(value);
    notify(stored ? 'Ключ подключён. Можно отправлять сообщения и оставлять отзывы.' : 'Ключ подключён до обновления страницы: хранилище браузера недоступно.');
  }, [notify]);

  useEffect(() => {
    const navigate = () => setPath(location.pathname);
    const expired = () => { disconnect(); notify('Для отправки сообщений и отзывов войдите снова.'); };
    window.addEventListener('popstate', navigate);
    window.addEventListener('session-expired', expired);
    return () => {
      window.removeEventListener('popstate', navigate);
      window.removeEventListener('session-expired', expired);
    };
  }, [disconnect, notify]);

  useEffect(() => {
    if (!session) return;
    const checkExpiration = () => {
      if (session.expiresAt <= Date.now()) { disconnect(); notify('Срок действия ключа истёк.'); }
    };
    const timer = setInterval(checkExpiration, 1000);
    checkExpiration();
    return () => clearInterval(timer);
  }, [session, disconnect, notify]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(''), 5500);
    return () => clearTimeout(timer);
  }, [toast]);

  const detail = path.match(/^\/concert\/([^/]+)\/?$/);
  return <>
    <a className="skip-link" href="#main">Перейти к содержанию</a>
    <header className="site-header">
      <div className="header-inner">
        <Link to="/" className="brand" aria-label="Музыкальный понедельник — на главную">
          <span className="brand-mark" aria-hidden="true">м<span>п</span><i /></span>
          <span>музыкальный<br />понедельник</span>
        </Link>
        <Link to="/" className="header-afisha" aria-current={path === '/' ? 'page' : undefined}>Афиша клуба</Link>
        {session
          ? <button className="login-button" onClick={() => { disconnect(); notify('Вы вышли из клуба.'); }}><Icon name="logout" size={17} />Выйти</button>
          : <button className="login-button" onClick={openAuth}><Icon name="user" size={17} />Войти в клуб<Icon name="arrow" size={17} /></button>}
      </div>
    </header>
    <main id="main" tabIndex={-1}>
      {detail
        ? <Concert key={detail[1]} id={detail[1]} session={session} openAuth={openAuth} notify={notify} />
        : path === '/'
          ? <Home openAuth={openAuth} />
          : <div className="container not-found"><span className="eyebrow">404</span><h1>Страница не найдена</h1><Link to="/" className="button">Вернуться к афише<Icon name="arrow" /></Link></div>}
    </main>
    <footer className="site-footer container"><Link to="/">Музыкальный понедельник</Link><span>Клуб слушателей · Георгиевский зал</span></footer>
    {showAuth && <AuthModal onClose={closeAuth} onConnect={connect} />}
    {toast && <div className="toast" role="status"><Icon name="note" size={18} /><span>{toast}</span><button aria-label="Закрыть уведомление" onClick={() => setToast('')}><Icon name="close" size={16} /></button></div>}
  </>;
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>);
