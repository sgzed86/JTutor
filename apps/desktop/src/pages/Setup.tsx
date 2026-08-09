import { useEffect, useState } from "react";
import { api } from "../api";

export default function Setup() {
  const [health, setHealth] = useState<any>(null);
  const [err, setErr] = useState("");
  const [logLines, setLogLines] = useState<string[]>([]);
  const [logPath, setLogPath] = useState("");

  async function refresh() {
    try {
      setHealth(await api.health());
      setErr("");
    } catch (e: any) {
      setErr(e.message || String(e));
      setHealth(null);
    }
  }

  async function refreshLog() {
    try {
      const tail = await api.logTail(150);
      setLogPath(tail.path);
      setLogLines(tail.lines);
    } catch (e: any) {
      setLogLines([`Could not load log: ${e.message || e}`]);
    }
  }

  useEffect(() => {
    refresh();
    refreshLog();
  }, []);

  return (
    <div className="stack">
      <div>
        <h1>Setup</h1>
        <p className="muted">Local services required for full tutor + voice.</p>
      </div>
      {err && <div className="panel">Backend unreachable: {err}</div>}
      <div className="panel stack">
        <div className="row">
          <span className={`pill ${health ? "ok" : "bad"}`}>API :8765</span>
          <span className={`pill ${health?.ollama?.ok ? "ok" : "bad"}`}>Ollama</span>
          <span className={`pill ${health?.voicevox?.ok ? "ok" : "bad"}`}>VoiceVox</span>
          <span className={`pill ${health?.whisper?.ok ? "ok" : "bad"}`}>Whisper</span>
          <button className="btn" onClick={refresh}>Refresh</button>
        </div>
        {health?.ollama?.models && (
          <p className="muted">Models: {(health.ollama.models || []).join(", ") || "(none)"}</p>
        )}
        {health?.settings?.log_path && (
          <p className="muted">Debug log: <code>{health.settings.log_path}</code></p>
        )}
      </div>
      <div className="panel stack">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>Session log</h2>
          <button className="btn" onClick={refreshLog}>Refresh log</button>
        </div>
        <p className="muted" style={{ margin: 0 }}>
          API + tutor UI events (for debugging). File: {logPath || "…"}
        </p>
        <pre
          style={{
            margin: 0,
            maxHeight: 320,
            overflow: "auto",
            fontSize: "0.75rem",
            background: "var(--bg2)",
            padding: "0.75rem",
            borderRadius: 8,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {logLines.length ? logLines.join("\n") : "(empty — use the tutor, then refresh)"}
        </pre>
      </div>
      <div className="panel">
        <h2>Checklist</h2>
        <ol>
          <li>Install <a href="https://ollama.com/" target="_blank">Ollama</a> and pull a model: <code>ollama pull qwen2.5:7b</code></li>
          <li>Install & start <a href="https://voicevox.hiroshiba.jp/" target="_blank">VOICEVOX</a> (engine on port 50021)</li>
          <li>Keep Irodori PDF + MP3s under <code>assets/</code> (already organized)</li>
          <li>Python deps: <code>pip install -r backend/requirements.txt</code></li>
          <li>Run <code>npm run dev</code> from the repo root</li>
        </ol>
      </div>
    </div>
  );
}
