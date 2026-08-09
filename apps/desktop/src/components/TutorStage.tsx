import { TutorMascot, type MascotMood } from "./TutorMascot";
import { ModeCard } from "./ModeCard";
import { PronunciationFeedback } from "./PronunciationFeedback";
import type { TutorStageModel } from "../lib/tutorDisplay";

type Props = {
  model: TutorStageModel;
  mood: MascotMood;
  status: string;
  expectSpeech: boolean;
  recording: boolean;
  speaking: boolean;
  busy: boolean;
  onMicClick: () => void;
  onStopSpeaking?: () => void;
  lastGrade?: any;
  activity?: any;
  step?: any;
};

export function TutorStage({
  model,
  mood,
  status,
  expectSpeech,
  recording,
  speaking,
  busy,
  onMicClick,
  onStopSpeaking,
  lastGrade,
  activity,
  step,
}: Props) {
  const bubbleJp = model.tutorBubbleJp || "…";
  const lineClass =
    model.lineColor === "orange"
      ? "say-target-orange"
      : model.lineColor === "yellow"
        ? "say-target-yellow"
        : "";

  const presenceHint = speaking
    ? "Yuki is saying this line — listen, then respond when prompted."
    : recording
      ? "Yuki is waiting for your answer."
      : expectSpeech
        ? "Your turn — say the phrase below."
        : null;

  return (
    <div className="tutor-stage panel">
      <div className="tutor-stage-header">
        <span className="pill">{model.activityLabel}</span>
        <span className="pill accent">{model.stepLabel}</span>
      </div>

      <p className="tutor-instruction">{model.instructionEn || model.hintEn || status}</p>

      <ModeCard
        bookMode={step?.book_mode || activity?.book_mode}
        bookSubstep={step?.book_substep}
        pictureHasImage={activity?.picture_has_image ?? !!activity?.picture_hint_en}
      />

      <div className="tutor-conversation">
        <TutorMascot mood={mood} />

        <div className="tutor-dialogue">
          <div className="tutor-speech-bubble tutor-speech-bubble-live">
            <span className="tutor-speech-label">Yuki</span>
            <p className="tutor-speech-jp">{bubbleJp}</p>
            {(model.tutorBubbleEn || model.hintEn) && (
              <p className="tutor-speech-en muted">{model.tutorBubbleEn || model.hintEn}</p>
            )}
          </div>
          {presenceHint && <p className="tutor-presence-hint muted">{presenceHint}</p>}

          {model.pictureHint && !model.showSayCard && (
            <div className="tutor-picture-hint">
              <span className="tutor-picture-label">In the book</span>
              <p>{model.pictureHint}</p>
            </div>
          )}
        </div>
      </div>

      {model.showShadowCard && (
        <div className="shadow-card">
          <div className="say-target-header">
            <span className="say-target-label">Shadow now</span>
            <span className="pill">Not graded</span>
          </div>
          <p className="say-target-jp" style={{ fontSize: "1.35rem" }}>
            Speak quietly along with the CD
          </p>
          <p className="say-target-alt muted">
            Follow the dialog in your book. When the audio ends, role-play begins.
          </p>
        </div>
      )}

      {model.showSayCard && (
        <div className={`say-target-card ${lineClass} ${model.listenPreview ? "preview" : ""}`}>
          <div className="say-target-header">
            <span className="say-target-label">{model.sayLabel}</span>
            {model.listenPreview && <span className="pill">Coming up</span>}
            {model.lineColor === "orange" && (
              <span className="book-color-tag orange">Orange line</span>
            )}
          </div>
          {model.pictureHint && (
            <p className="say-target-picture muted">{model.pictureHint}</p>
          )}
          {model.sayTargetJp ? (
            <p className="say-target-jp">{model.sayTargetJp}</p>
          ) : (
            <p className="say-target-jp muted">Open the book and follow the CD</p>
          )}
          {model.sayAlternates.length > 0 && (
            <p className="say-target-alt muted">
              Also OK: {model.sayAlternates.slice(0, 4).join(" · ")}
            </p>
          )}
          <PronunciationFeedback grade={lastGrade} visible={!!lastGrade} />
        </div>
      )}

      <div className="tutor-stage-actions">
        <p className="tutor-status-line">{status}</p>
        {speaking && onStopSpeaking && (
          <button type="button" className="btn" onClick={onStopSpeaking}>
            Stop speaking
          </button>
        )}
        {expectSpeech && (
          <button
            type="button"
            className={`btn primary tutor-mic-btn ${recording ? "danger" : ""}`}
            disabled={busy}
            onClick={onMicClick}
          >
            {recording ? "Done speaking" : "Tap to speak"}
          </button>
        )}
      </div>
    </div>
  );
}
