import type { Notice } from "../../state/useTutorSession";

/**
 * Errors are transient and actionable. The old red banner set itself from
 * thirteen places, cleared from four, and stayed pinned for the rest of the
 * lesson after a single hiccup.
 */
export function NoticeStack({ notices, onDismiss }: { notices: Notice[]; onDismiss: (id: number) => void }) {
  if (!notices.length) return null;
  return (
    <div className="notices" role="region" aria-label="Notifications">
      {notices.map((notice) => (
        <div className="notice" data-severity={notice.severity} key={notice.id} role="status">
          <div className="notice__body">
            <span className="notice__message">{notice.message}</span>
            {notice.hint && <span className="notice__hint">{notice.hint}</span>}
            {notice.action && (
              <button type="button" className="btn btn--ghost btn--icon" onClick={notice.action.run}>
                {notice.action.label}
              </button>
            )}
          </div>
          <button type="button" className="notice__close" onClick={() => onDismiss(notice.id)} aria-label="Dismiss">
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
