import { useRef } from "react";
import type { Grade } from "../../api/types";

/**
 * The grader already computed `hits`, `gaps`, `best_match`, the transcript and a
 * character-level diff; the old UI showed only a rounded percentage. Space is
 * reserved so a result appearing never reflows the stage.
 */
export function GradeResult({
  grade,
  recordingUrl,
  onHearTarget,
}: {
  grade: Grade | null;
  recordingUrl: string | null;
  onHearTarget: () => void;
}) {
  const playbackRef = useRef<HTMLAudioElement | null>(null);

  if (!grade) {
    return <div className="grade" data-passed="none" aria-hidden style={{ visibility: "hidden" }} />;
  }

  const score = Math.round(grade.score ?? grade.similarity ?? 0);
  const passed = grade.passed === true;

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

      <div className="grade__actions">
        <button type="button" className="btn btn--ghost btn--icon" onClick={onHearTarget}>
          <span aria-hidden>🔊</span> Hear it again
        </button>
        <button
          type="button"
          className="btn btn--ghost btn--icon"
          onClick={playRecording}
          disabled={!recordingUrl}
        >
          <span aria-hidden>🎙</span> Hear me
        </button>
      </div>
    </div>
  );
}
