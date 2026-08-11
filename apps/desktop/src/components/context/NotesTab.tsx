import type { TutorPayload } from "../../api/types";

export function NotesTab({ payload }: { payload: TutorPayload | null }) {
  const grammar = payload?.grammar ?? [];
  const canDos = payload?.can_dos ?? [];

  return (
    <>
      <section>
        <p className="rail__section-title">Can-dos in this lesson</p>
        {canDos.length === 0 && <p className="ask__empty">This lesson has no Can-do checks.</p>}
        {canDos.map((cd) => (
          <div className="note-item" key={cd.id} style={{ marginBottom: "var(--sp-3)" }}>
            <span className="note-item__title">{cd.statement_en}</span>
            {cd.statement_jp && <span className="muted jp">{cd.statement_jp}</span>}
            <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
              {cd.mastered ? "Mastered" : `Best ${Math.round(cd.best_score ?? 0)}%`}
            </span>
          </div>
        ))}
      </section>

      <section>
        <p className="rail__section-title">Grammar</p>
        {grammar.length === 0 && <p className="ask__empty">No grammar worksheet for this lesson.</p>}
        {grammar.map((g, i) => (
          <div className="note-item" key={i} style={{ marginBottom: "var(--sp-2)" }}>
            <span className="note-item__title jp">{g.point}</span>
            {g.pattern_en && <span className="muted">{g.pattern_en}</span>}
            {g.prompt_en && (
              <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
                {g.prompt_en}
              </span>
            )}
          </div>
        ))}
      </section>
    </>
  );
}
