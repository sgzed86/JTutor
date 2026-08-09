import type { TutorPayload } from "../../api/types";

export function WordsTab({ payload, onSpeak }: { payload: TutorPayload | null; onSpeak: (t: string) => void }) {
  const phrases = payload?.activity?.key_phrases ?? [];
  const vocab = (payload?.vocab ?? []).filter((v) => v.jp);

  if (!phrases.length && !vocab.length) {
    return <p className="ask__empty">No vocabulary for this step.</p>;
  }

  return (
    <>
      {phrases.length > 0 && (
        <section>
          <p className="rail__section-title">This activity</p>
          {phrases.map((phrase) => (
            <div className="word-row" key={phrase}>
              <span className="word-row__jp">{phrase}</span>
              <button type="button" className="btn btn--ghost btn--icon" onClick={() => onSpeak(phrase)}>
                <span aria-hidden>🔊</span>
                <span className="visually-hidden">Hear {phrase}</span>
              </button>
            </div>
          ))}
        </section>
      )}

      {vocab.length > 0 && (
        <section>
          <p className="rail__section-title">Lesson vocabulary</p>
          {vocab.slice(0, 60).map((item, i) => (
            <div className="word-row" key={`${item.jp}-${i}`}>
              <span>
                <span className="word-row__jp">{item.jp}</span>
                {item.en && <span className="word-row__en"> — {item.en}</span>}
              </span>
              <button type="button" className="btn btn--ghost btn--icon" onClick={() => onSpeak(item.jp as string)}>
                <span aria-hidden>🔊</span>
                <span className="visually-hidden">Hear {item.jp}</span>
              </button>
            </div>
          ))}
        </section>
      )}
    </>
  );
}
