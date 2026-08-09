type Grade = {
  passed?: boolean;
  score?: number;
  similarity?: number;
  feedback_en?: string;
  feedback_jp?: string;
  best_match?: string | null;
  hits?: string[];
};

type Props = {
  grade: Grade | null | undefined;
  visible?: boolean;
};

export function PronunciationFeedback({ grade, visible }: Props) {
  if (!visible || !grade) return null;
  const score = grade.score ?? grade.similarity ?? 0;
  const passed = grade.passed === true;
  return (
    <div className={`pronunciation-feedback ${passed ? "ok" : "retry"}`} role="status">
      <div className="pronunciation-feedback-row">
        <span className="pronunciation-score">{Math.round(score)}%</span>
        <span className="pronunciation-label">{passed ? "Match" : "Try again"}</span>
      </div>
      <p className="pronunciation-text">{grade.feedback_en || (passed ? "Good pronunciation." : "Adjust and retry.")}</p>
      {!passed && grade.best_match && (
        <p className="pronunciation-target muted">Target: {grade.best_match}</p>
      )}
    </div>
  );
}
