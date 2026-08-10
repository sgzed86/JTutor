import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import type { TutorStageModel } from "../../lib/tutorDisplay";

export const CHECK_BLANKS_EVENT = "jtutor-check-blanks";

/** Split a cloze prompt on ＿ runs so we can render inputs between segments. */
export function splitBlankPrompt(prompt: string): string[] {
  return prompt.split(/＿+/);
}

export function fillBlankPrompt(prompt: string, fills: string[]): string {
  const parts = splitBlankPrompt(prompt);
  let out = parts[0] ?? "";
  for (let i = 0; i < parts.length - 1; i += 1) {
    out += (fills[i] || "").trim();
    out += parts[i + 1] ?? "";
  }
  return out;
}

/**
 * One card for the thing the learner is meant to look at: the phrase to say, the
 * shadowing prompt, picture hint, or typed fill-in blanks.
 */
export function FocusCard({
  model,
  onPlayTarget,
  onSubmitText,
  textSubmitDisabled,
}: {
  model: TutorStageModel;
  onPlayTarget: (text: string) => void;
  onSubmitText?: (text: string) => void;
  textSubmitDisabled?: boolean;
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

  if (model.focus === "fill") {
    return (
      <BlankFillCard
        model={model}
        onSubmitText={onSubmitText}
        disabled={textSubmitDisabled}
      />
    );
  }

  if (model.focus === "choose") {
    return <ChooseCard model={model} onSubmitText={onSubmitText} disabled={textSubmitDisabled} />;
  }

  if (model.focus === "note") {
    return <NoteCard model={model} onSubmitText={onSubmitText} disabled={textSubmitDisabled} />;
  }

  if (model.focus === "kanji_study") {
    return (
      <div className="focus-card" data-variant="kanji-study">
        <div className="focus-card__head">
          <span className="focus-card__label">{model.sayLabel}</span>
          <span className="pill">漢字のことば</span>
        </div>
        <div className="kanji-grid">
          {model.kanjiItems.map((it) => (
            <button
              key={it.kanji}
              type="button"
              className="kanji-card"
              onClick={() => onPlayTarget(it.reading || it.kanji)}
            >
              <span className="kanji-card__kanji jp">{it.kanji}</span>
              {it.reading && <span className="kanji-card__reading jp">{it.reading}</span>}
              {it.gloss_en && <span className="kanji-card__gloss">{it.gloss_en}</span>}
            </button>
          ))}
        </div>
        <p className="focus-card__alt">Tap a card to hear it. Then tap Next to read the example lines.</p>
      </div>
    );
  }

  if (model.focus === "kanji_type") {
    return <KanjiTypeCard model={model} onSubmitText={onSubmitText} disabled={textSubmitDisabled} />;
  }

  if (model.focus === "passage") {
    return (
      <div className="focus-card" data-variant="passage">
        <div className="focus-card__head">
          <span className="focus-card__label">{model.sayLabel}</span>
          <span className="pill">Read</span>
        </div>
        {model.passageJp && <p className="focus-card__jp jp">{model.passageJp}</p>}
        {model.passageEn && <p className="focus-card__alt focus-card__passage">{model.passageEn}</p>}
        <p className="focus-card__alt">Tap Next when you are ready to continue.</p>
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
      {model.glossEn && <p className="focus-card__alt">{model.glossEn}</p>}
      <p className="focus-card__jp jp">{model.sayTargetJp ?? "Open your book and follow the CD"}</p>
      {model.sayAlternates.length > 0 && (
        <p className="focus-card__alt">Also fine: {model.sayAlternates.slice(0, 4).join(" · ")}</p>
      )}
    </div>
  );
}

function BlankFillCard({
  model,
  onSubmitText,
  disabled,
}: {
  model: TutorStageModel;
  onSubmitText?: (text: string) => void;
  disabled?: boolean;
}) {
  const prompt = model.blankPromptJp || "";
  const parts = useMemo(() => splitBlankPrompt(prompt || "＿"), [prompt]);
  const slotCount = Math.max(parts.length - 1, model.blankCount, 1);
  const [fills, setFills] = useState<string[]>(() => Array.from({ length: slotCount }, () => ""));
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    setFills(Array.from({ length: slotCount }, () => ""));
  }, [prompt, slotCount, model.blankIndex]);

  useEffect(() => {
    const onCheck = () => formRef.current?.requestSubmit();
    window.addEventListener(CHECK_BLANKS_EVENT, onCheck);
    return () => window.removeEventListener(CHECK_BLANKS_EVENT, onCheck);
  }, []);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!onSubmitText || disabled) return;
    const rebuilt = prompt ? fillBlankPrompt(prompt, fills) : fills.map((f) => f.trim()).filter(Boolean).join("");
    const fallback = fills.map((f) => f.trim()).filter(Boolean).join("");
    const text = (rebuilt || fallback).trim();
    if (!text) return;
    onSubmitText(text);
  };

  return (
    <div className="focus-card" data-variant="fill">
      <div className="focus-card__head">
        <span className="focus-card__label">{model.sayLabel}</span>
        <span className="pill">Type your answer</span>
      </div>
      <form ref={formRef} className="blank-fill" onSubmit={submit}>
        <p className="blank-fill__prompt jp" aria-label="Fill in the blanks">
          {parts.map((part, i) => (
            <span key={`p-${i}`}>
              {part}
              {i < slotCount && (
                <input
                  className="blank-fill__input jp"
                  value={fills[i] ?? ""}
                  onChange={(ev) => {
                    const next = [...fills];
                    next[i] = ev.target.value;
                    setFills(next);
                  }}
                  size={Math.max(2, Math.min(12, (fills[i] || "").length + 2))}
                  autoFocus={i === 0}
                  autoComplete="off"
                  spellCheck={false}
                  aria-label={`Blank ${i + 1}`}
                  disabled={disabled}
                />
              )}
            </span>
          ))}
        </p>
        <div className="blank-fill__actions">
          <button type="submit" className="btn btn--primary" disabled={disabled || fills.every((f) => !f.trim())}>
            Check answers
          </button>
        </div>
      </form>
      <p className="focus-card__alt">Use Japanese input. Replay Tutor/CD if you want to hear it again.</p>
    </div>
  );
}

function ChooseCard({
  model,
  onSubmitText,
  disabled,
}: {
  model: TutorStageModel;
  onSubmitText?: (text: string) => void;
  disabled?: boolean;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    setSelected([]);
  }, [model.choices, model.sayLabel]);

  useEffect(() => {
    const onCheck = () => formRef.current?.requestSubmit();
    window.addEventListener(CHECK_BLANKS_EVENT, onCheck);
    return () => window.removeEventListener(CHECK_BLANKS_EVENT, onCheck);
  }, []);

  const toggle = (id: string) => {
    if (model.chooseMulti) {
      setSelected((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]));
    } else {
      setSelected([id]);
    }
  };

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!onSubmitText || disabled || !selected.length) return;
    onSubmitText(selected.join(","));
  };

  return (
    <div className="focus-card" data-variant="choose">
      <div className="focus-card__head">
        <span className="focus-card__label">{model.sayLabel}</span>
        <span className="pill">{model.chooseMulti ? "Select all" : "Choose one"}</span>
      </div>
      {model.passageEn && <p className="focus-card__alt">{model.passageEn}</p>}
      <form ref={formRef} className="choice-list" onSubmit={submit}>
        {model.choices.map((c) => {
          const active = selected.includes(c.id);
          return (
            <button
              key={c.id}
              type="button"
              className={`choice-list__item${active ? " is-active" : ""}`}
              onClick={() => toggle(c.id)}
              disabled={disabled}
              aria-pressed={active}
            >
              <span className="choice-list__id">{c.id}</span>
              <span className="choice-list__label jp">{c.label_jp || c.label_en || c.id}</span>
            </button>
          );
        })}
        <div className="blank-fill__actions">
          <button type="submit" className="btn btn--primary" disabled={disabled || !selected.length}>
            Check answers
          </button>
        </div>
      </form>
    </div>
  );
}

function NoteCard({
  model,
  onSubmitText,
  disabled,
}: {
  model: TutorStageModel;
  onSubmitText?: (text: string) => void;
  disabled?: boolean;
}) {
  const [text, setText] = useState("");
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    setText("");
  }, [model.sayLabel]);

  useEffect(() => {
    const onCheck = () => formRef.current?.requestSubmit();
    window.addEventListener(CHECK_BLANKS_EVENT, onCheck);
    return () => window.removeEventListener(CHECK_BLANKS_EVENT, onCheck);
  }, []);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!onSubmitText || disabled || !text.trim()) return;
    onSubmitText(text.trim());
  };

  return (
    <div className="focus-card" data-variant="note">
      <div className="focus-card__head">
        <span className="focus-card__label">{model.sayLabel}</span>
        <span className="pill">Type notes</span>
      </div>
      <form ref={formRef} className="note-form" onSubmit={submit}>
        <textarea
          className="note-form__input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          placeholder="Who / what / where…"
          disabled={disabled}
        />
        <div className="blank-fill__actions">
          <button type="submit" className="btn btn--primary" disabled={disabled || !text.trim()}>
            Save notes
          </button>
        </div>
      </form>
    </div>
  );
}

function KanjiTypeCard({
  model,
  onSubmitText,
  disabled,
}: {
  model: TutorStageModel;
  onSubmitText?: (text: string) => void;
  disabled?: boolean;
}) {
  const prompt = model.kanjiPrompt;
  const [text, setText] = useState("");
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    setText("");
  }, [prompt?.kanji, prompt?.index]);

  useEffect(() => {
    const onCheck = () => formRef.current?.requestSubmit();
    window.addEventListener(CHECK_BLANKS_EVENT, onCheck);
    return () => window.removeEventListener(CHECK_BLANKS_EVENT, onCheck);
  }, []);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!onSubmitText || disabled || !text.trim()) return;
    onSubmitText(text.trim());
  };

  return (
    <div className="focus-card" data-variant="kanji-type">
      <div className="focus-card__head">
        <span className="focus-card__label">{model.sayLabel}</span>
        <span className="pill">Type with IME</span>
      </div>
      <div className="kanji-type__prompt">
        {prompt?.reading && <p className="kanji-type__reading jp">{prompt.reading}</p>}
        {prompt?.gloss_en && <p className="focus-card__alt">{prompt.gloss_en}</p>}
        <p className="focus-card__alt">Type the kanji for this reading (変換 is OK).</p>
      </div>
      <form ref={formRef} className="note-form" onSubmit={submit}>
        <input
          className="kanji-type__input jp"
          value={text}
          onChange={(e) => setText(e.target.value)}
          autoFocus
          autoComplete="off"
          spellCheck={false}
          disabled={disabled}
          placeholder="漢字"
        />
        <div className="blank-fill__actions">
          <button type="submit" className="btn btn--primary" disabled={disabled || !text.trim()}>
            Check
          </button>
          {prompt?.reading && (
            <button type="button" className="btn btn--ghost" onClick={() => onSubmitText?.(prompt.reading || "")} disabled={disabled}>
              Use reading
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
