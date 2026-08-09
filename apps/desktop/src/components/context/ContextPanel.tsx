import { useState } from "react";
import type { TutorPayload } from "../../api/types";
import { AskYukiTab } from "./AskYukiTab";
import { NotesTab } from "./NotesTab";
import { ScriptTab } from "./ScriptTab";
import { WordsTab } from "./WordsTab";

type Tab = "ask" | "notes" | "script" | "words";

const TABS: { id: Tab; label: string }[] = [
  { id: "ask", label: "Ask Yuki" },
  { id: "notes", label: "Notes" },
  { id: "script", label: "Script" },
  { id: "words", label: "Words" },
];

export function ContextPanel({
  payload,
  asking,
  onAsk,
  onCancelAsk,
  onAskByVoice,
  recordingQuestion,
  onSpeak,
}: {
  payload: TutorPayload | null;
  asking: boolean;
  onAsk: (text: string) => void;
  onCancelAsk: () => void;
  onAskByVoice: () => void;
  recordingQuestion: boolean;
  onSpeak: (text: string) => void;
}) {
  const [tab, setTab] = useState<Tab>("ask");

  return (
    <aside className="context" aria-label="Lesson context">
      <div className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="tabpanel" role="tabpanel">
        {tab === "ask" && (
          <AskYukiTab
            messages={payload?.help_messages ?? []}
            asking={asking}
            recording={recordingQuestion}
            onAsk={onAsk}
            onCancel={onCancelAsk}
            onAskByVoice={onAskByVoice}
          />
        )}
        {tab === "notes" && <NotesTab payload={payload} />}
        {tab === "script" && <ScriptTab payload={payload} onSpeak={onSpeak} />}
        {tab === "words" && <WordsTab payload={payload} onSpeak={onSpeak} />}
      </div>
    </aside>
  );
}
