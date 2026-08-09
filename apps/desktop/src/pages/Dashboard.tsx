import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Dashboard() {
  const [progress, setProgress] = useState<any[]>([]);
  const [bookTitle, setBookTitle] = useState("");
  const [srs, setSrs] = useState({ due: 0, total: 0 });
  const [health, setHealth] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [p, s, h] = await Promise.all([
          api.progress(),
          api.srsStats(),
          api.health(),
        ]);
        setProgress(p.lessons || []);
        setBookTitle(p.book_title || p.book_id || "");
        setSrs(s);
        setHealth(h);
      } catch (e: any) {
        setErr(e.message || String(e));
      }
    })();
  }, []);

  const current =
    progress.find((l) => l.unlocked && !l.mastered && l.lesson_id !== "L00") ||
    progress.find((l) => l.lesson_id === "L01" || l.lesson_id === "EL01");

  return (
    <div className="stack">
      <div>
        <h1>今日もいっしょに</h1>
        <p className="muted">
          Study {bookTitle || "Irodori"} with a local tutor, voice, and SRS.
        </p>
      </div>
      {err && <div className="panel" style={{ borderColor: "var(--danger)" }}>{err} — start the backend, then refresh.</div>}
      <div className="grid-2">
        <div className="panel stack">
          <h2>Current lesson</h2>
          {current ? (
            <>
              <h3>{current.lesson_id} · {current.title_en}</h3>
              <p className="muted">{current.topic_en}</p>
              <p>
                Can-dos mastered:{" "}
                {(current.can_dos || []).filter((c: any) => c.mastered).length}/
                {(current.can_dos || []).length}
              </p>
              <div className="row">
                <Link className="btn primary" to={`/tutor/${current.lesson_id}`}>
                  Continue lesson
                </Link>
                <Link className="btn" to="/progress">
                  Progress map
                </Link>
              </div>
            </>
          ) : (
            <p className="muted">Loading…</p>
          )}
        </div>
        <div className="stack">
          <div className="panel">
            <h2>SRS due</h2>
            <p style={{ fontSize: "2rem", margin: "0.4rem 0", fontFamily: "var(--font-display)" }}>
              {srs.due}
            </p>
            <p className="muted">{srs.total} cards total</p>
            <Link className="btn ok" to="/srs">
              Review now
            </Link>
          </div>
          <div className="panel">
            <h2>Services</h2>
            <div className="row" style={{ marginTop: "0.5rem" }}>
              <span className={`pill ${health?.backend ? "ok" : "bad"}`}>Backend</span>
              <span className={`pill ${health?.ollama?.ok ? "ok" : "bad"}`}>Ollama</span>
              <span className={`pill ${health?.voicevox?.ok ? "ok" : "bad"}`}>VoiceVox</span>
              <span className={`pill ${health?.whisper?.ok ? "ok" : "bad"}`}>Whisper</span>
            </div>
            <p className="muted" style={{ marginTop: "0.75rem" }}>
              <Link to="/setup">Setup checklist</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
