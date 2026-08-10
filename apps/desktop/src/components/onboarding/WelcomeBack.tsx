import { Dialog } from "../ui/Dialog";
import type { ResumeHint } from "../../api/types";

/**
 * Shown once per app launch when we know where the learner left off.
 * Continues into that lesson (tutor resumes the session) or lets them browse.
 */
export function WelcomeBack({
  open,
  resume,
  bookTitle,
  onContinue,
  onBrowse,
}: {
  open: boolean;
  resume: ResumeHint;
  bookTitle?: string;
  onContinue: () => void;
  onBrowse: () => void;
}) {
  const title = resume.title_en || resume.lesson_id;
  const returning = Boolean(resume.has_session);
  const pct = Math.max(0, Math.min(100, Math.round(resume.percent ?? 0)));

  return (
    <Dialog
      open={open}
      title={returning ? "Welcome back" : "Ready to learn"}
      onClose={onBrowse}
      narrow
      footer={
        <>
          <button type="button" className="btn btn--ghost" onClick={onBrowse}>
            Browse lessons
          </button>
          <button type="button" className="btn btn--primary" onClick={onContinue}>
            {returning ? "Continue" : "Start"} {resume.lesson_id}
          </button>
        </>
      }
    >
      <div className="welcome-back">
        <p className="welcome-back__lead">
          {returning
            ? "Pick up where you left off — your place in the lesson is saved."
            : `Start with ${resume.lesson_id}. You can switch lessons anytime from the left rail.`}
        </p>
        <div className="welcome-back__card">
          <span className="welcome-back__id">{resume.lesson_id}</span>
          <span className="welcome-back__title">{title}</span>
          {bookTitle && <span className="welcome-back__book muted">{bookTitle}</span>}
          <span className="welcome-back__phase">
            {resume.phase_label || resume.phase_hint || "In progress"}
            {returning && pct > 0 ? ` · ${pct}%` : ""}
          </span>
          {returning && (
            <div className="welcome-back__bar" aria-hidden>
              <i style={{ width: `${pct}%` }} />
            </div>
          )}
        </div>
      </div>
    </Dialog>
  );
}
