import type { TutorPayload } from "../../api/types";

/**
 * The dialog script is the clean source (it comes from the YAML). Whisper
 * transcripts of the CD tracks are shown underneath when the build ships them,
 * clearly labelled because they are machine-generated and noisy.
 */
export function ScriptTab({ payload, onSpeak }: { payload: TutorPayload | null; onSpeak: (t: string) => void }) {
  const step = payload?.step;
  const lines = step?.dialog_script ?? payload?.activity?.dialog_script ?? [];
  const audio = step?.audio ?? [];
  const transcripts = audio.filter((a) => a.transcript);

  if (!lines.length && !transcripts.length) {
    return <p className="ask__empty">No script for this step. Role-play activities show the dialog here.</p>;
  }

  return (
    <>
      {lines.length > 0 && (
        <section>
          <p className="rail__section-title">Dialog</p>
          {lines.map((line, i) => (
            <div className="script-line" data-speaker={line.speaker} key={i}>
              <span className="script-line__who">{line.speaker === "partner" ? "Partner" : "You"}</span>
              <button
                type="button"
                className="btn btn--ghost"
                style={{ justifyContent: "flex-start", padding: 0 }}
                onClick={() => onSpeak(line.jp)}
              >
                <span className="jp">{line.jp}</span>
              </button>
            </div>
          ))}
        </section>
      )}

      {transcripts.length > 0 && (
        <section>
          <p className="rail__section-title">Audio transcript (auto-generated)</p>
          {transcripts.map((entry) => (
            <div className="note-item" key={entry.path} style={{ marginBottom: "var(--sp-2)" }}>
              <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
                {entry.path.split("/").pop()}
              </span>
              <span className="jp">{entry.transcript}</span>
            </div>
          ))}
        </section>
      )}
    </>
  );
}
