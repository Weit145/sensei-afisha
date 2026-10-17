import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { hash, time, weekday, dateShort } from './utils.js';
import { mediaUrl } from './api.js';

export function Icon({ name, size = 20, ...props }) {
  const paths = {
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" /></>,
    moon: <path d="M20.8 13.1A9 9 0 0 1 10.9 3.2a9 9 0 1 0 9.9 9.9Z" />,
    arrow: <><path d="M4 12h15m-6-6 6 6-6 6" /></>,
    back: <path d="m14 5-7 7 7 7M7 12h14" />,
    search: <><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></>,
    heart: <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z" />,
    pin: <><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M7 3v4m10-4v4M3 11h18m-14 4h3m4 0h3" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    close: <path d="m6 6 12 12M6 18 18 6" />,
    check: <path d="m5 12 4 4L19 6" />,
    send: <><path d="m22 2-7 20-4-9L2 9 22 2ZM11 13 22 2" /></>,
    chat: <path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z" />,
    user: <><circle cx="12" cy="8" r="4" /><path d="M4 21v-2a8 8 0 0 1 16 0v2" /></>,
    share: <><path d="M12 16V3m-5 5 5-5 5 5M5 13v7h14v-7" /></>,
    refresh: <><path d="M20 7v5h-5M4 17v-5h5" /><path d="M6.1 6a8 8 0 0 1 13.3 3M4.6 15A8 8 0 0 0 18 18" /></>,
    note: <><path d="M9 18V5l12-3v13M9 8l12-3" /><ellipse cx="6" cy="18" rx="3" ry="2.5" /><ellipse cx="18" cy="15" rx="3" ry="2.5" /></>,
    star: <path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9L12 3Z" />,
    logout: <><path d="M9 4H4v16h5m5-4 4-4-4-4m-6 4h10" /></>,
    external: <><path d="M14 3h7v7m0-7L10 14M10 3H3v18h18v-7" /></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name] || paths.note}</svg>;
}

export function Link({ to, children, onClick, ...props }) {
  return <a href={to} {...props} onClick={event => {
    onClick?.(event);
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (`${location.pathname}${location.search}` === to) return;
    history.pushState({}, '', to);
    window.dispatchEvent(new PopStateEvent('popstate'));
    window.scrollTo({ top: 0, behavior: 'instant' });
  }}>{children}</a>;
}

export function Modal({ title, children, onClose, className = '' }) {
  const ref = useRef(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const id = useId();
  useLayoutEffect(() => {
    const oldFocus = document.activeElement;
    const oldOverflow = document.body.style.overflow;
    const root = document.getElementById('root');
    const oldInert = root?.inert;
    if (root) root.inert = true;
    document.body.style.overflow = 'hidden';
    const dialog = ref.current;
    (dialog.querySelector('input:not([disabled]), textarea:not([disabled])') || dialog).focus();
    const keyDown = event => {
      if (event.key === 'Escape') closeRef.current();
      if (event.key !== 'Tab') return;
      const focusable = [...dialog.querySelectorAll('a[href], button, input, textarea, select, [tabindex="0"]')].filter(el => !el.disabled && el.offsetParent !== null);
      const first = focusable[0], last = focusable.at(-1);
      if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialog || !dialog.contains(document.activeElement))) { event.preventDefault(); first?.focus(); }
      if (!first) { event.preventDefault(); dialog.focus(); }
    };
    document.addEventListener('keydown', keyDown);
    return () => { document.body.style.overflow = oldOverflow; if (root) root.inert = oldInert; document.removeEventListener('keydown', keyDown); if (oldFocus?.isConnected) oldFocus.focus(); else document.getElementById('main')?.focus(); };
  }, []);
  useLayoutEffect(() => {
    const dialog = ref.current;
    if (dialog && !dialog.contains(document.activeElement)) dialog.focus();
  });
  return createPortal(<div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <section ref={ref} className={`modal ${className}`} role="dialog" aria-modal="true" aria-labelledby={id} tabIndex={-1}>
      <button className="icon-button modal-close" aria-label="Закрыть окно" onClick={onClose}><Icon name="close" /></button>
      <div className="eyebrow">КЛУБ МУЗЫКАЛЬНОГО ПОНЕДЕЛЬНИКА</div>
      <h2 id={id}>{title}</h2>
      {children}
    </section>
  </div>, document.body);
}

export function ErrorState({ message, retry, compact = false }) {
  return <div className={`empty-state ${compact ? 'compact' : ''}`} role="alert">
    <span className="empty-icon"><Icon name="note" size={28} /></span>
    <h3>Небольшая пауза</h3><p>{message}</p>
    {retry && <button className="button secondary" onClick={retry}><Icon name="refresh" size={17} />Попробовать ещё раз</button>}
  </div>;
}

export function Poster({ event, featured = false, retryKey = 0, onImageError, showRetry = true }) {
  const [failed, setFailed] = useState(false);
  const [loading, setLoading] = useState(true);
  const imageRef = useRef(null);
  const image = mediaUrl(event.cover_url || event.images?.find(image => image.is_cover)?.image_url || event.images?.[0]?.image_url);
  useLayoutEffect(() => {
    setFailed(false);
    setLoading(Boolean(image && !(imageRef.current?.complete && imageRef.current.naturalWidth > 0)));
  }, [image, retryKey]);
  const variant = hash(event.id) % 4;
  const uid = useId().replaceAll(':', '');
  return <div className={`poster poster-${variant} ${featured ? 'poster-featured' : ''}`}>
    {image && !failed ? <><img ref={imageRef} src={image} alt={`Афиша: ${event.title}`} loading={featured ? 'eager' : 'lazy'} onLoad={() => setLoading(false)} onError={() => { setLoading(false); setFailed(true); onImageError?.(); }} />{loading && <span className="poster-loading" role="status">Загружаем постер…</span>}</> : <>
      <div className="poster-top"><span>МУЗЫКАЛЬНЫЕ<br />ПОНЕДЕЛЬНИКИ</span><span>ЖИВОЙ<br />ЗВУК</span></div>
      <svg className="poster-art" viewBox="0 0 440 330" fill="none" aria-hidden="true">
        <defs><clipPath id={uid}><rect x="24" y="0" width="392" height="330" /></clipPath></defs>
        <g clipPath={`url(#${uid})`}>
          {variant === 0 && <><circle cx="220" cy="165" r="133" fill="currentColor" opacity=".15" />{Array.from({ length: 17 }, (_, i) => <path key={i} d={`M${68 + i * 19} 340V${153 - Math.sin(i / 16 * Math.PI) * 130}Q220 ${-155 + i * 3} ${372 - i * 6} 340`} stroke="currentColor" strokeWidth="1.5" />)}<circle cx="220" cy="165" r="45" fill="currentColor" /><circle cx="220" cy="165" r="11" fill="var(--poster-bg)" /></>}
          {variant === 1 && <>{Array.from({ length: 10 }, (_, i) => <ellipse key={i} cx="220" cy="167" rx={30 + i * 15} ry={30 + i * 15} transform={`rotate(${i * 9} 220 167)`} stroke="currentColor" strokeWidth="1.2" />)}<path d="M80 245 220 45l140 200H80Z" fill="var(--poster-bg)" /><path d="M220 45v200" stroke="currentColor" strokeWidth="1.4" /><circle cx="220" cy="245" r="49" fill="currentColor" /></>}
          {variant === 2 && <><path d="M80 290V133a140 140 0 0 1 280 0v157H80Z" fill="currentColor" opacity=".9" />{Array.from({ length: 9 }, (_, i) => <path key={i} d={`M${101 + i * 27} 140v165`} stroke="var(--poster-bg)" strokeWidth="1.5" />)}{[0, 1, 3, 4, 5, 7].map(i => <path key={i} d={`M${114 + i * 27} 140v95`} stroke="var(--poster-bg)" strokeWidth="12" />)}<path d="M80 133a140 140 0 0 1 280 0" stroke="currentColor" strokeWidth="2" /><circle cx="220" cy="85" r="24" fill="var(--poster-bg)" /></>}
          {variant === 3 && <><ellipse cx="220" cy="170" rx="79" ry="146" transform="rotate(35 220 170)" fill="currentColor" opacity=".9" /><ellipse cx="220" cy="170" rx="79" ry="146" transform="rotate(-35 220 170)" stroke="currentColor" strokeWidth="2" />{Array.from({ length: 7 }, (_, i) => <path key={i} d={`M${110 + i * 35} 20v300`} stroke="var(--poster-bg)" strokeWidth="1.5" />)}<circle cx="220" cy="170" r="25" fill="var(--poster-bg)" /></>}
        </g>
      </svg>
      <div className="poster-bottom"><span>{dateShort(event.starts_at)}</span><span>{time(event.starts_at)}</span></div>
    </>}
    {image && failed && showRetry && <div className="poster-error" role="alert"><span>Не удалось загрузить постер.</span><button className="inline-button" onClick={() => { setFailed(false); setLoading(true); }}>Повторить загрузку</button></div>}
    {event.status === 'cancelled' && <span className="poster-status">Концерт отменён</span>}
  </div>;
}

export function DateLine({ event }) {
  return <span className="date-line">{dateShort(event.starts_at)}<span className="dot" />{time(event.starts_at)}<span className="weekday">, {weekday(event.starts_at)}</span></span>;
}
