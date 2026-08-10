import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import type { TutorPayload } from "../../api/types";

export type BookPageProps = {
  payload: TutorPayload;
  /** Larger stage presentation vs compact context-tab look. */
  variant?: "stage" | "panel";
  className?: string;
};

/**
 * Renders one textbook/worksheet page as a JPEG from the backend.
 * Electron cannot reliably embed the full 100MB+ PDFs in an iframe.
 */
export function BookPage({ payload, variant = "panel", className }: BookPageProps) {
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);

  const which = payload.state === "grammar" ? "grammar" : "textbook";
  const pages = payload.pdf_pages ?? payload.lesson_meta?.pdf_pages ?? [];
  const page = payload.book_page ?? pages[0] ?? null;
  const rangeLabel =
    pages.length >= 2 ? `${pages[0]}–${pages[pages.length - 1]}` : pages.length === 1 ? `${pages[0]}` : null;

  const imageSrc = useMemo(() => {
    if (!page) return null;
    return api.pdfPageUrl(which, { bookId: payload.book_id, page, scale: variant === "stage" ? 2 : 1.6 });
  }, [payload.book_id, which, page, variant]);

  const fullPdfSrc = useMemo(
    () => api.pdfUrl(which, { bookId: payload.book_id, page }),
    [payload.book_id, which, page],
  );

  useEffect(() => {
    setReady(false);
    setFailed(false);
  }, [imageSrc]);

  if (!page || !imageSrc) {
    return (
      <div className={`book-page book-page--empty ${className ?? ""}`}>
        <p className="ask__empty">No page preview for this step — keep your paper book nearby.</p>
      </div>
    );
  }

  return (
    <div className={`book-page book-page--${variant} ${className ?? ""}`} data-ready={ready ? "1" : "0"}>
      <header className="book-page__meta">
        <div className="book-page__meta-text">
          <span className="book-page__title">
            {which === "grammar" ? "Worksheet" : "Textbook"} · p. {page}
          </span>
          <span className="muted book-page__sub">
            {rangeLabel && which === "textbook" ? `Lesson ${rangeLabel}` : null}
            {payload.activity?.book_activity != null && which === "textbook"
              ? `${rangeLabel ? " · " : ""}Activity ${payload.activity.book_activity}`
              : null}
          </span>
        </div>
        <a className="btn btn--ghost btn--icon book-page__open" href={fullPdfSrc} target="_blank" rel="noreferrer">
          Full PDF
        </a>
      </header>

      {failed ? (
        <div className="book-page__fallback">
          <p className="ask__empty">Couldn&apos;t load this page.</p>
          <a className="btn btn--ghost" href={fullPdfSrc} target="_blank" rel="noreferrer">
            Open full PDF
          </a>
        </div>
      ) : (
        <div className="book-page__scroll">
          {!ready && <p className="muted book-page__loading">Loading page…</p>}
          <img
            key={imageSrc}
            className="book-page__image"
            src={imageSrc}
            alt={`${which === "grammar" ? "Worksheet" : "Textbook"} page ${page}`}
            onLoad={() => setReady(true)}
            onError={() => setFailed(true)}
          />
        </div>
      )}
    </div>
  );
}

export function payloadHasBookPage(payload: TutorPayload | null | undefined): boolean {
  if (!payload) return false;
  const page = payload.book_page ?? payload.pdf_pages?.[0] ?? payload.lesson_meta?.pdf_pages?.[0];
  return Boolean(page);
}

export function shouldShowBookOnStage(payload: TutorPayload | null | undefined): boolean {
  if (!payloadHasBookPage(payload)) return false;
  const state = payload?.state;
  return state === "book" || state === "grammar" || state === "lesson_intro";
}
