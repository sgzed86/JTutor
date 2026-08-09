import { useState } from "react";

type Props = {
  open: boolean;
  canDoId: string;
  statementEn?: string;
  statementJp?: string;
  busy?: boolean;
  onSubmit: (stars: number, comment: string) => void;
  onSkip: () => void;
};

export function SelfCheckModal({
  open,
  canDoId,
  statementEn,
  statementJp,
  busy,
  onSubmit,
  onSkip,
}: Props) {
  const [stars, setStars] = useState(2);
  const [comment, setComment] = useState("");

  if (!open) return null;

  return (
    <div className="self-check-backdrop" role="dialog" aria-modal="true" aria-labelledby="self-check-title">
      <div className="self-check-modal panel stack">
        <h2 id="self-check-title" style={{ margin: 0 }}>
          Can-do self-check
        </h2>
        <p className="muted" style={{ margin: 0, fontSize: "0.88rem" }}>
          Soft rating only — unlock still uses the graded role-play.
        </p>
        {statementJp && (
          <p style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: "1.05rem" }}>{statementJp}</p>
        )}
        {statementEn && <p className="muted" style={{ margin: 0 }}>{statementEn}</p>}

        <div className="self-check-stars" role="group" aria-label="Star rating">
          {[1, 2, 3].map((n) => (
            <button
              key={n}
              type="button"
              className={`self-check-star ${stars >= n ? "on" : ""}`}
              onClick={() => setStars(n)}
              disabled={busy}
              aria-label={`${n} star${n > 1 ? "s" : ""}`}
            >
              ★
            </button>
          ))}
        </div>
        <p className="muted" style={{ margin: 0, fontSize: "0.82rem" }}>
          {stars === 1 && "I tried, but need more practice."}
          {stars === 2 && "I did it."}
          {stars === 3 && "I did it well."}
        </p>

        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={2}
          placeholder="Optional comment (what felt hard / easy)"
          disabled={busy}
          style={{
            width: "100%",
            resize: "vertical",
            background: "var(--bg2)",
            color: "var(--ink)",
            border: "1px solid var(--line)",
            borderRadius: 8,
            padding: "0.5rem 0.65rem",
          }}
        />

        <div className="row" style={{ justifyContent: "flex-end", gap: "0.5rem" }}>
          <button type="button" className="btn" disabled={busy} onClick={onSkip}>
            Skip
          </button>
          <button
            type="button"
            className="btn primary"
            disabled={busy || !canDoId}
            onClick={() => onSubmit(stars, comment)}
          >
            {busy ? "Saving…" : "Save rating"}
          </button>
        </div>
      </div>
    </div>
  );
}
