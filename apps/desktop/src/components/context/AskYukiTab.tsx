import { useState } from "react";
import type { Message } from "../../api/types";

/**
 * Asking a question never blocks the stage: the spinner and cancel live here,
 * and the lesson controls stay live while Ollama thinks.
 */
export function AskYukiTab({
  messages,
  asking,
  recording,
  onAsk,
  onCancel,
  onAskByVoice,
}: {
  messages: Message[];
  asking: boolean;
  recording: boolean;
  onAsk: (text: string) => void;
  onCancel: () => void;
  onAskByVoice: () => void;
}) {
  const [text, setText] = useState("");

  const submit = () => {
    const value = text.trim();
    if (!value) return;
    onAsk(value);
    setText("");
  };

  return (
    <>
      <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
        Stuck? Ask in English or Japanese. You stay on the same exercise.
      </p>

      <div className="ask__log">
        {messages.length === 0 && (
          <p className="ask__empty">No questions yet. Try “What should I say here?”</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className="ask__bubble" data-role={m.role}>
            {m.role === "assistant" ? (
              <>
                <p className="jp">{m.content}</p>
                {m.hint_en && <p className="muted">{m.hint_en}</p>}
              </>
            ) : (
              <p>{m.content}</p>
            )}
          </div>
        ))}
        {asking && (
          <div className="ask__bubble" data-role="assistant">
            <span className="spinner" aria-hidden /> Yuki is thinking…
          </div>
        )}
      </div>

      <div className="ask__form">
        <label className="visually-hidden" htmlFor="ask-input">
          Your question
        </label>
        <textarea
          id="ask-input"
          className="textarea"
          rows={2}
          value={text}
          placeholder="What does おはよう mean?"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
        />
        <div className="ask__actions">
          <button type="button" className="btn btn--primary" onClick={submit} disabled={!text.trim() || asking}>
            Send
          </button>
          <button type="button" className="btn" onClick={onAskByVoice} disabled={asking}>
            {recording ? "Stop" : "Ask by voice"}
          </button>
          {asking && (
            <button type="button" className="btn btn--ghost" onClick={onCancel}>
              Cancel
            </button>
          )}
        </div>
      </div>
    </>
  );
}
