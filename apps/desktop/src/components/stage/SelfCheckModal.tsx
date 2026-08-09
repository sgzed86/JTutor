import { useState } from "react";
import { Dialog } from "../ui/Dialog";

const CAPTIONS: Record<number, string> = {
  1: "I tried, but I need more practice.",
  2: "I did it.",
  3: "I did it well.",
};

export function SelfCheckModal({
  open,
  statementEn,
  statementJp,
  busy,
  onSubmit,
  onSkip,
}: {
  open: boolean;
  statementEn?: string;
  statementJp?: string;
  busy?: boolean;
  onSubmit: (stars: number, comment: string) => void;
  onSkip: () => void;
}) {
  const [stars, setStars] = useState(2);
  const [comment, setComment] = useState("");

  return (
    <Dialog
      open={open}
      narrow
      title="How did that go?"
      onClose={onSkip}
      labelledBy="self-check-title"
      footer={
        <>
          <button type="button" className="btn btn--ghost" onClick={onSkip} disabled={busy}>
            Skip
          </button>
          <button
            type="button"
            className="btn btn--primary"
            disabled={busy}
            onClick={() => {
              onSubmit(stars, comment);
              setComment("");
            }}
          >
            {busy ? "Saving…" : "Save"}
          </button>
        </>
      }
    >
      <p className="muted">
        Your own rating. It is recorded for you — unlocking still uses the graded role-play.
      </p>
      {statementJp && <p className="jp" style={{ fontSize: "var(--fs-lg)" }}>{statementJp}</p>}
      {statementEn && <p className="muted">{statementEn}</p>}

      <div className="stars" role="group" aria-label="Star rating">
        {[1, 2, 3].map((n) => (
          <button
            key={n}
            type="button"
            className="star"
            data-on={stars >= n}
            aria-label={`${n} star${n > 1 ? "s" : ""}`}
            aria-pressed={stars === n}
            onClick={() => setStars(n)}
            disabled={busy}
          >
            ★
          </button>
        ))}
      </div>
      <p className="muted" style={{ textAlign: "center" }}>
        {CAPTIONS[stars]}
      </p>

      <label className="field">
        <span className="field__label">Anything that felt hard? (optional)</span>
        <textarea
          className="textarea"
          rows={2}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          disabled={busy}
        />
      </label>
    </Dialog>
  );
}
