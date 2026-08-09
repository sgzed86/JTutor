import type { TutorStageModel } from "../../lib/tutorDisplay";

/**
 * One card for the thing the learner is meant to look at: the phrase to say, the
 * shadowing prompt, or the picture hint. Replaces three near-duplicate blocks
 * and reserves its height so the layout never jumps between steps.
 */
export function FocusCard({
  model,
  onPlayTarget,
}: {
  model: TutorStageModel;
  onPlayTarget: (text: string) => void;
}) {
  if (model.focus === "none") {
    return <div className="focus-card" data-variant="none" aria-hidden style={{ visibility: "hidden" }} />;
  }

  if (model.focus === "shadow") {
    return (
      <div className="focus-card" data-variant="shadow">
        <div className="focus-card__head">
          <span className="focus-card__label">Shadow now</span>
          <span className="pill">Not graded</span>
        </div>
        <p className="focus-card__jp jp">CDに合わせて、小声で</p>
        <p className="focus-card__alt">Speak quietly along with the audio. Role-play starts when it ends.</p>
      </div>
    );
  }

  if (model.focus === "picture") {
    return (
      <div className="focus-card" data-variant="picture">
        <span className="focus-card__label">In the book</span>
        <p className="focus-card__alt">{model.pictureHint}</p>
      </div>
    );
  }

  const preview = model.focus === "listen-preview";
  return (
    <div className="focus-card" data-variant={model.focus} data-line={model.lineColor ?? undefined}>
      <div className="focus-card__head">
        <span className="focus-card__label">{model.sayLabel}</span>
        {preview && <span className="pill">Coming up</span>}
        {model.lineColor === "orange" && <span className="pill">Orange line</span>}
        {model.sayTargetJp && (
          <button
            type="button"
            className="btn btn--ghost btn--icon"
            onClick={() => onPlayTarget(model.sayTargetJp as string)}
          >
            <span aria-hidden>🔊</span> Hear it
          </button>
        )}
      </div>
      {model.pictureHint && <p className="focus-card__alt">{model.pictureHint}</p>}
      <p className="focus-card__jp jp">{model.sayTargetJp ?? "Open your book and follow the CD"}</p>
      {model.sayAlternates.length > 0 && (
        <p className="focus-card__alt">Also fine: {model.sayAlternates.slice(0, 4).join(" · ")}</p>
      )}
    </div>
  );
}
