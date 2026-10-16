import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { hash, time, weekday, dateShort } from './utils.js';
import { mediaUrl } from './api.js';

export function Icon({ name, size = 20, ...props }) {
  const paths = {
    arrow: <><path d="M4 12h15m-6-6 6 6-6 6" /></>,
    back: <path d="m14 5-7 7 7 7M7 12h14" />,
    pin: <><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M7 3v4m10-4v4M3 11h18m-14 4h3m4 0h3" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    close: <path d="m6 6 12 12M6 18 18 6" />,
    check: <path d="m5 12 4 4L19 6" />,
    send: <><path d="m22 2-7 20-4-9L2 9 22 2ZM11 13 22 2" /></>,
    chat: <path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z" />,
    user: <><circle cx="12" cy="8" r="4" /><path d="M4 21v-2a8 8 0 0 1 16 0v2" /></>,
    refresh: <><path d="M20 7v5h-5M4 17v-5h5" /><path d="M6.1 6a8 8 0 0 1 13.3 3M4.6 15A8 8 0 0 0 18 18" /></>,
    note: <><path d="M9 18V5l12-3v13M9 8l12-3" /><ellipse cx="6" cy="18" rx="3" ry="2.5" /><ellipse cx="18" cy="15" rx="3" ry="2.5" /></>,
    star: <path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9L12 3Z" />,
    logout: <><path d="M9 4H4v16h5m5-4 4-4-4-4m-6 4h10" /></>,
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
  const id = useId();
  useEffect(() => {
    const oldFocus = document.activeElement;
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const dialog = ref.current;
    (dialog.querySelector('input, textarea, button') || dialog).focus();
    const keyDown = event => {
      if (event.key === 'Escape') onClose();
      if (event.key !== 'Tab') return;
      const focusable = [...dialog.querySelectorAll('a[href], button, input, textarea, select, [tabindex="0"]')].filter(el => !el.disabled && el.offsetParent !== null);
      const first = focusable[0], last = focusable.at(-1);
      if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener('keydown', keyDown);
    return () => { document.body.style.overflow = oldOverflow; document.removeEventListener('keydown', keyDown); oldFocus?.focus(); };
  }, [onClose]);
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

export function Poster({ event, featured = false }) {
  const [failed, setFailed] = useState(false);
  const image = mediaUrl(event.cover_url || event.images?.find(image => image.is_cover)?.image_url || event.images?.[0]?.image_url);
  useEffect(() => setFailed(false), [image]);
  const variant = hash(event.id) % 4;
  return <div className={`poster poster-${variant} ${featured ? 'poster-featured' : ''}`}>
    {image && !failed ? <img src={image} alt={`Постер концерта: ${event.title}`} loading={featured ? 'eager' : 'lazy'} onError={() => setFailed(true)} /> : <div className="poster-fallback">
      <span className="poster-label">МУЗЫКАЛЬНЫЕ<br />ПОНЕДЕЛЬНИКИ</span>
      <svg className="poster-art" viewBox="0 0 400 320" fill="none" aria-hidden="true">
        {Array.from({ length: 10 }, (_, i) => <ellipse key={i} cx="200" cy="160" rx={32 + i * 15} ry={32 + i * 12} transform={`rotate(${i * 7 - 30} 200 160)`} stroke="currentColor" opacity=".7" />)}
        <circle cx="200" cy="160" r="31" fill="currentColor" />
        <circle cx="200" cy="160" r="7" fill="var(--poster-bg)" />
      </svg>
      <div className="poster-caption"><span>{dateShort(event.starts_at)} · {time(event.starts_at)}</span><strong>{event.title}</strong></div>
    </div>}
    {event.status === 'cancelled' && <span className="poster-status">Концерт отменён</span>}
  </div>;
}

export function DateLine({ event }) {
  return <span className="date-line">{dateShort(event.starts_at)}<span className="dot" />{time(event.starts_at)}<span className="weekday">, {weekday(event.starts_at)}</span></span>;
}
