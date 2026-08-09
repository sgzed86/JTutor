import { useCallback, useEffect, useMemo, useState } from "react";
import { api, type VoiceSpeakerOption } from "../../../api";
import { speakTutor } from "../../../speech";

const PREVIEW_LINE = "こんにちは。わたしは ゆき です。いっしょに 日本語を べんきょうしましょう。";

export default function VoiceSettings() {
  const [options, setOptions] = useState<VoiceSpeakerOption[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.voiceSpeakers();
      setOptions(data.options || []);
      setSelectedId(data.selected_speaker_id ?? null);
      if (!(data.options || []).length) {
        setError("No VoiceVox speakers found. Is VoiceVox running?");
      }
    } catch (e: any) {
      setError(e.message || String(e));
      setOptions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedLabel = useMemo(() => {
    const opt = options.find((o) => o.speaker_id === selectedId);
    return opt?.label || (selectedId != null ? `Speaker ${selectedId}` : "—");
  }, [options, selectedId]);

  async function onSelect(speakerId: number) {
    setSaving(true);
    setError("");
    setStatus("");
    try {
      const res = await api.setVoiceSpeaker(speakerId);
      setSelectedId(res.selected_speaker_id);
      setStatus(`Tutor voice set to ${options.find((o) => o.speaker_id === speakerId)?.label || speakerId}`);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setSaving(false);
    }
  }

  async function preview() {
    if (previewing) return;
    setPreviewing(true);
    setError("");
    try {
      await speakTutor(PREVIEW_LINE, api.speak);
      setStatus("Preview finished.");
    } catch (e: any) {
      setError("Preview failed: " + (e.message || e));
    } finally {
      setPreviewing(false);
    }
  }

  return (
    <div className="panel stack">
      <div>
        <h2 style={{ margin: 0 }}>Tutor Voice</h2>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          Choose a VoiceVox character and style for Yuki. All tutor lines use this voice.
        </p>
      </div>

      {error && (
        <div className="panel" style={{ borderColor: "var(--danger)", margin: 0 }}>
          {error}
        </div>
      )}

      {loading ? (
        <p className="muted">Loading speakers from VoiceVox…</p>
      ) : (
        <>
          <label className="stack" style={{ gap: "0.35rem" }}>
            <span style={{ fontSize: "0.9rem" }}>Speaker / style</span>
            <select
              value={selectedId ?? ""}
              disabled={saving || !options.length}
              onChange={(e) => {
                const id = Number(e.target.value);
                if (!Number.isNaN(id)) void onSelect(id);
              }}
              style={{
                background: "var(--bg2)",
                color: "var(--ink)",
                border: "1px solid var(--line)",
                borderRadius: 10,
                padding: "0.55rem 0.75rem",
                maxWidth: 480,
              }}
            >
              {!options.length && <option value="">No speakers</option>}
              {options.map((o) => (
                <option key={o.speaker_id} value={o.speaker_id}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <p className="muted" style={{ margin: 0, fontSize: "0.88rem" }}>
            Current: <strong style={{ color: "var(--ink)" }}>{selectedLabel}</strong>
          </p>

          <div className="row" style={{ gap: "0.5rem" }}>
            <button
              type="button"
              className="btn primary"
              disabled={previewing || saving || selectedId == null}
              onClick={() => void preview()}
            >
              {previewing ? "Playing…" : "Preview Voice"}
            </button>
            <button type="button" className="btn" disabled={loading || saving} onClick={() => void load()}>
              Refresh list
            </button>
          </div>

          {status && <p className="muted" style={{ margin: 0 }}>{status}</p>}
        </>
      )}
    </div>
  );
}
