type Progress = {
  percent?: number;
  fraction?: number;
  label?: string;
  phase?: string;
};

type Props = {
  progress: Progress | null | undefined;
};

export function LessonProgressBar({ progress }: Props) {
  if (!progress) return null;
  const pct = progress.percent ?? Math.round((progress.fraction ?? 0) * 100);
  return (
    <div className="lesson-progress" aria-label={`Lesson progress ${pct} percent`}>
      <div className="lesson-progress-labels">
        <span className="muted">Lesson progress</span>
        <span>{progress.label || progress.phase || ""}</span>
        <span className="lesson-progress-pct">{pct}%</span>
      </div>
      <div className="lesson-progress-track">
        <div className="lesson-progress-fill" style={{ width: `${Math.min(100, pct)}%` }} />
      </div>
    </div>
  );
}
