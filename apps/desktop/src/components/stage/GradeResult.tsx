import { useRef } from "react";
import type { Grade } from "../../api/types";

/**
 * The grader already computed `hits`, `gaps`, `best_match`, the transcript and a
 * character-level diff. After a miss on speech, recovery is a choice — not an
 * automatic CD replay.
 */
export function GradeResult({
  grade,
  recordingUrl,
  offerRetryHelp,
  hasBookRecording,
  onHearTarget,
  onHearBook,
  onTryAgain,
}: {
  grade: Grade | null;
  recordingUrl: string | null;
  offerRetryHelp?: boolean;
  hasBookRecording?: boolean;
  onHearTarget: () => void;
  onHearBook?: () => void;
  onTryAgain?: () => void;
}) {
  const playbackRef = useRef<HTMLAudioElement | null>(null);

  if (!grade) {
    return <div className="grade" data-passed="none" aria-hidden style={{ visibility: "hidden" }} />;
  }

  const score = Math.round(grade.score ?? grade.similarity ?? 0);
  const passed = grade.passed === true;
  const showChoices = !passed && Boolean(offerRetryHelp);

  const playRecording = () => {
    if (!recordingUrl) return;
    if (!playbackRef.current) playbackRef.current = new Audio();
    playbackRef.current.src = recordingUrl;
    void playbackRef.current.play().catch(() => undefined);
  };

  return (
    <div className="grade" data-passed={passed} role="status">
      <div className="grade__row">
        <span className="grade__score">{score}%</span>
        <span className="grade__verdict">{passed ? "Match" : "Try again"}</span>
        <span className="grade__heard">{grade.feedback_en || grade.jp_feedback || ""}</span>
      </div>

      {grade.transcript && (
        <p className="grade__heard">
          Heard: <span className="jp">{grade.transcript}</span>
        </p>
      )}

      {!passed && grade.diff && grade.diff.length > 0 && (
        <p className="grade__diff jp">
          {grade.diff.map((run, i) => (
            <mark key={i} data-miss={!run.match}>
              {run.text}
            </mark>
          ))}
        </p>
      )}

      {showChoices ? (
        <div className="grade__retry" role="group" aria-label="What next?">
          <p className="grade__retry-label">What next?</p>
          <div className="grade__actions">
            {hasBookRecording && onHearBook && (
              <button type="button" className="btn btn--ghost btn--icon" onClick={onHearBook}>
                Hear the recording
              </button>
            )}
            <button type="button" className="btn btn--ghost btn--icon" onClick={onHearTarget}>
              Hear Yuki say it
            </button>
            <button type="button" className="btn btn--primary btn--icon" onClick={onTryAgain}>
              Try again
            </button>
          </div>
          {recordingUrl && (
            <button type="button" className="btn btn--ghost btn--icon" onClick={playRecording}>
              Hear me
            </button>
          )}
        </div>
      ) : (
        <div className="grade__actions">
          <button type="button" className="btn btn--ghost btn--icon" onClick={onHearTarget}>
            Hear it again
          </button>
          <button
            type="button"
            className="btn btn--ghost btn--icon"
            onClick={playRecording}
            disabled={!recordingUrl}
          >
            Hear me
          </button>
        </div>
      )}
    </div>
  );
}
