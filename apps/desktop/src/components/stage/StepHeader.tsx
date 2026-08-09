import type { TutorStageModel } from "../../lib/tutorDisplay";

/**
 * Where the learner is: activity position, mode, sub-step, and a segmented bar
 * for the current activity. The segments come from `step.substeps`, which the
 * server now sends — the client used to have no way to know how long an
 * activity was.
 */
export function StepHeader({ model }: { model: TutorStageModel }) {
  const { substeps, substepIndex } = model;

  return (
    <header className="step-header">
      <div className="step-header__row">
        <span className="pill">{model.activityLabel}</span>
        <span className="pill pill--accent">
          <span aria-hidden>{model.modeIcon}</span>
          {model.modeTitle}
        </span>
        {model.stepLabel && <span className="pill">{model.stepLabel}</span>}
      </div>

      {model.segmentLabel && <p className="step-header__segment">{model.segmentLabel}</p>}

      {substeps.length > 1 && (
        <div
          className="substeps"
          role="progressbar"
          aria-valuemin={1}
          aria-valuemax={substeps.length}
          aria-valuenow={(substepIndex ?? 0) + 1}
          aria-label={`Step ${(substepIndex ?? 0) + 1} of ${substeps.length} in this activity`}
        >
          {substeps.map((name, i) => (
            <span
              key={`${name}-${i}`}
              className="substeps__seg"
              data-state={
                substepIndex === null ? "todo" : i < substepIndex ? "done" : i === substepIndex ? "current" : "todo"
              }
            />
          ))}
        </div>
      )}
    </header>
  );
}
