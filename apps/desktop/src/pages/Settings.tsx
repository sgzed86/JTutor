import VoiceSettings from "../components/Settings/VoiceSettings";
import { api } from "../api";

export default function Settings() {
  return (
    <div className="stack">
      <div>
        <h1>Settings</h1>
        <p className="muted">Tutor voice and local service defaults.</p>
      </div>

      <VoiceSettings />

      <div className="panel stack">
        <h2 style={{ margin: 0 }}>Environment defaults</h2>
        <p className="muted" style={{ margin: 0 }}>
          These are read from the backend process / <code>.env</code>. Voice selection above overrides the speaker at runtime.
        </p>
        <p>
          <strong>API</strong>: {api.base}
        </p>
        <p>
          <strong>Ollama model</strong>: set <code>OLLAMA_MODEL</code> (default qwen2.5:7b)
        </p>
        <p>
          <strong>Default VoiceVox speaker</strong>: set <code>SELECTED_SPEAKER_ID</code> or{" "}
          <code>VOICEVOX_SPEAKER</code> (default 2)
        </p>
        <p>
          <strong>Whisper model</strong>: set <code>WHISPER_MODEL</code> (default small)
        </p>
        <p>
          <strong>Mastery</strong>: pass each Can-do role-play once (spoken, score ≥ 80) to finish the lesson
        </p>
        <p>
          <a className="btn" href={api.pdfUrl("starter")} target="_blank" rel="noreferrer">
            Open starter PDF
          </a>{" "}
          <a className="btn" href={api.pdfUrl("grammar")} target="_blank" rel="noreferrer">
            Open grammar PDF
          </a>
        </p>
      </div>
    </div>
  );
}
