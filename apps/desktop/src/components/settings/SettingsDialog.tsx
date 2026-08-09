import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import type { Health, VoiceSpeakerOption } from "../../api/types";
import { useSettings } from "../../state/useSettings";
import { Dialog } from "../ui/Dialog";
import { Segmented, SettingRow, Slider, Toggle } from "../ui/controls";
import { MicCheck } from "./MicCheck";

type Section = "voice" | "audio" | "appearance" | "lessons" | "ask" | "advanced";

const SECTIONS: { id: Section; label: string }[] = [
  { id: "voice", label: "Voice" },
  { id: "audio", label: "Audio" },
  { id: "appearance", label: "Appearance" },
  { id: "lessons", label: "Lessons" },
  { id: "ask", label: "Ask Yuki" },
  { id: "advanced", label: "Advanced" },
];

export function SettingsDialog({
  open,
  onClose,
  health,
}: {
  open: boolean;
  onClose: () => void;
  health: Health | null;
}) {
  const { settings, update, reset } = useSettings();
  const [section, setSection] = useState<Section>("voice");
  const [speakers, setSpeakers] = useState<VoiceSpeakerOption[]>([]);
  const [speakerError, setSpeakerError] = useState<string | null>(null);
  const [outputs, setOutputs] = useState<MediaDeviceInfo[]>([]);
  const [previewing, setPreviewing] = useState(false);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    api
      .voiceSpeakers(controller.signal)
      .then((data) => {
        setSpeakers(data.options);
        setSpeakerError(null);
      })
      .catch((err) => setSpeakerError(err?.message ?? "VOICEVOX isn't running."));
    navigator.mediaDevices
      ?.enumerateDevices()
      .then((devices) => setOutputs(devices.filter((d) => d.kind === "audiooutput")))
      .catch(() => undefined);
    return () => controller.abort();
  }, [open]);

  const groupedSpeakers = useMemo(() => {
    const byName = new Map<string, VoiceSpeakerOption[]>();
    for (const option of speakers) {
      const list = byName.get(option.name) ?? [];
      list.push(option);
      byName.set(option.name, list);
    }
    return Array.from(byName.entries());
  }, [speakers]);

  const preview = async () => {
    setPreviewing(true);
    try {
      const blob = await api.speak("こんにちは。わたしは ゆき です。いっしょに べんきょうしましょう。");
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      await audio.play();
      audio.onended = () => URL.revokeObjectURL(url);
    } catch {
      setSpeakerError("Preview failed — VOICEVOX isn't reachable.");
    } finally {
      setPreviewing(false);
    }
  };

  return (
    <Dialog
      open={open}
      title="Settings"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn btn--ghost" onClick={() => void reset()}>
            Reset to defaults
          </button>
          <button type="button" className="btn btn--primary" onClick={onClose}>
            Done
          </button>
        </>
      }
    >
      <div className="settings-layout">
        <nav className="settings-nav" aria-label="Settings sections">
          {SECTIONS.map((s) => (
            <button key={s.id} type="button" aria-current={section === s.id} onClick={() => setSection(s.id)}>
              {s.label}
            </button>
          ))}
        </nav>

        <div className="settings-section">
          {section === "voice" && (
            <>
              <SettingRow name="Tutor voice" hint="VOICEVOX character and style used for every tutor line.">
                <select
                  className="select"
                  style={{ maxWidth: 260 }}
                  value={settings.voice.speaker_id ?? ""}
                  disabled={!speakers.length}
                  onChange={(e) => {
                    const id = Number(e.target.value);
                    void api.setVoiceSpeaker(id);
                    void update({ voice: { speaker_id: id } });
                  }}
                >
                  {!speakers.length && <option value="">No voices available</option>}
                  {groupedSpeakers.map(([name, styles]) => (
                    <optgroup label={name} key={name}>
                      {styles.map((style) => (
                        <option key={style.speaker_id} value={style.speaker_id}>
                          {style.style_name}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </SettingRow>
              {speakerError && (
                <p className="settings-row__hint">
                  {speakerError} Lessons still work — Yuki is just silent.
                </p>
              )}
              <SettingRow name="Speaking rate">
                <Slider
                  label="Speaking rate"
                  value={settings.voice.speed}
                  min={0.7}
                  max={1.4}
                  step={0.05}
                  format={(v) => `${v.toFixed(2)}×`}
                  onChange={(speed) => void update({ voice: { speed } })}
                />
              </SettingRow>
              <SettingRow name="Pitch">
                <Slider
                  label="Pitch"
                  value={settings.voice.pitch}
                  min={-0.12}
                  max={0.12}
                  step={0.01}
                  format={(v) => v.toFixed(2)}
                  onChange={(pitch) => void update({ voice: { pitch } })}
                />
              </SettingRow>
              <SettingRow name="If VOICEVOX is off" hint="Fall back to the system voice instead of going silent.">
                <Toggle
                  label="Use system voice as fallback"
                  checked={settings.voice.fallback_to_system_voice}
                  onChange={(fallback_to_system_voice) => void update({ voice: { fallback_to_system_voice } })}
                />
              </SettingRow>
              <button type="button" className="btn" onClick={() => void preview()} disabled={previewing}>
                {previewing ? "Playing…" : "Preview voice"}
              </button>
            </>
          )}

          {section === "audio" && (
            <>
              <MicCheck
                deviceId={settings.audio.input_device_id}
                onSelectDevice={(input_device_id) => void update({ audio: { input_device_id } })}
              />
              <SettingRow name="Output device">
                <select
                  className="select"
                  style={{ maxWidth: 240 }}
                  value={settings.audio.output_device_id ?? ""}
                  onChange={(e) => void update({ audio: { output_device_id: e.target.value || null } })}
                >
                  <option value="">System default</option>
                  {outputs.map((device) => (
                    <option key={device.deviceId} value={device.deviceId}>
                      {device.label || "Output device"}
                    </option>
                  ))}
                </select>
              </SettingRow>
              <SettingRow name="Tutor volume">
                <Slider
                  label="Tutor volume"
                  value={settings.audio.tutor_volume}
                  min={0}
                  max={1}
                  step={0.05}
                  format={(v) => `${Math.round(v * 100)}%`}
                  onChange={(tutor_volume) => void update({ audio: { tutor_volume } })}
                />
              </SettingRow>
              <SettingRow name="Book audio volume">
                <Slider
                  label="Book audio volume"
                  value={settings.audio.book_volume}
                  min={0}
                  max={1}
                  step={0.05}
                  format={(v) => `${Math.round(v * 100)}%`}
                  onChange={(book_volume) => void update({ audio: { book_volume } })}
                />
              </SettingRow>
              <SettingRow name="Book audio speed" hint="Slow the CD down while you get used to it.">
                <Segmented
                  label="Book audio speed"
                  value={String(settings.audio.book_rate)}
                  options={[
                    { value: "0.75", label: "0.75×" },
                    { value: "1", label: "1×" },
                    { value: "1.25", label: "1.25×" },
                  ]}
                  onChange={(value) => void update({ audio: { book_rate: Number(value) } })}
                />
              </SettingRow>
            </>
          )}

          {section === "appearance" && (
            <>
              <SettingRow name="Theme">
                <Segmented
                  label="Theme"
                  value={settings.appearance.theme}
                  options={[
                    { value: "system", label: "System" },
                    { value: "light", label: "Light" },
                    { value: "dark", label: "Dark" },
                  ]}
                  onChange={(theme) => void update({ appearance: { theme } })}
                />
              </SettingRow>
              <SettingRow name="Text size">
                <Segmented
                  label="Text size"
                  value={settings.appearance.text_size}
                  options={[
                    { value: "normal", label: "Normal" },
                    { value: "large", label: "Large" },
                  ]}
                  onChange={(text_size) => void update({ appearance: { text_size } })}
                />
              </SettingRow>
              <SettingRow name="Japanese font">
                <Segmented
                  label="Japanese font"
                  value={settings.appearance.japanese_font}
                  options={[
                    { value: "mincho", label: "Mincho" },
                    { value: "gothic", label: "Gothic" },
                  ]}
                  onChange={(japanese_font) => void update({ appearance: { japanese_font } })}
                />
              </SettingRow>
              <SettingRow name="Reduce motion" hint="Also follows your operating system setting.">
                <Toggle
                  label="Reduce motion"
                  checked={settings.appearance.reduce_motion}
                  onChange={(reduce_motion) => void update({ appearance: { reduce_motion } })}
                />
              </SettingRow>
            </>
          )}

          {section === "lessons" && (
            <>
              <SettingRow name="Auto-advance" hint="After tutor audio, continue on its own.">
                <Segmented
                  label="Auto-advance"
                  value={settings.lessons.auto_advance}
                  options={[
                    { value: "off", label: "Off" },
                    { value: "after_audio", label: "After audio" },
                    { value: "after_audio_and_answer", label: "Always" },
                  ]}
                  onChange={(auto_advance) => void update({ lessons: { auto_advance } })}
                />
              </SettingRow>
              <SettingRow name="Auto-advance delay">
                <Slider
                  label="Auto-advance delay"
                  value={settings.lessons.auto_advance_delay_ms}
                  min={0}
                  max={3000}
                  step={100}
                  format={(v) => `${(v / 1000).toFixed(1)}s`}
                  onChange={(auto_advance_delay_ms) => void update({ lessons: { auto_advance_delay_ms } })}
                />
              </SettingRow>
              <SettingRow name="Start recording automatically" hint="When a step wants you to speak.">
                <Toggle
                  label="Auto-start recording"
                  checked={settings.lessons.auto_start_recording}
                  onChange={(auto_start_recording) => void update({ lessons: { auto_start_recording } })}
                />
              </SettingRow>
              <SettingRow name="Microphone button">
                <Segmented
                  label="Microphone button"
                  value={settings.lessons.mic_mode}
                  options={[
                    { value: "hold", label: "Hold" },
                    { value: "toggle", label: "Toggle" },
                  ]}
                  onChange={(mic_mode) => void update({ lessons: { mic_mode } })}
                />
              </SettingRow>
              <SettingRow name="Stop when I go quiet">
                <Toggle
                  label="Auto-stop on silence"
                  checked={settings.lessons.auto_stop_on_silence}
                  onChange={(auto_stop_on_silence) => void update({ lessons: { auto_stop_on_silence } })}
                />
              </SettingRow>
              <SettingRow name="Silence before stopping">
                <Slider
                  label="Silence before stopping"
                  value={settings.lessons.silence_ms}
                  min={600}
                  max={3000}
                  step={100}
                  format={(v) => `${(v / 1000).toFixed(1)}s`}
                  onChange={(silence_ms) => void update({ lessons: { silence_ms } })}
                />
              </SettingRow>
              <SettingRow
                name="Grading strictness"
                hint="Affects practice steps only. Can-do unlocks always use the same standard."
              >
                <Segmented
                  label="Grading strictness"
                  value={settings.lessons.grading_strictness}
                  options={[
                    { value: "lenient", label: "Lenient" },
                    { value: "standard", label: "Standard" },
                    { value: "strict", label: "Strict" },
                  ]}
                  onChange={(grading_strictness) => void update({ lessons: { grading_strictness } })}
                />
              </SettingRow>
            </>
          )}

          {section === "ask" && (
            <>
              <SettingRow name="Answer language">
                <Segmented
                  label="Answer language"
                  value={settings.ask_yuki.answer_language}
                  options={[
                    { value: "en", label: "English" },
                    { value: "ja", label: "Japanese" },
                    { value: "both", label: "Both" },
                  ]}
                  onChange={(answer_language) => void update({ ask_yuki: { answer_language } })}
                />
              </SettingRow>
              <SettingRow name="Answer length">
                <Segmented
                  label="Answer length"
                  value={settings.ask_yuki.answer_length}
                  options={[
                    { value: "brief", label: "Brief" },
                    { value: "normal", label: "Normal" },
                    { value: "detailed", label: "Detailed" },
                  ]}
                  onChange={(answer_length) => void update({ ask_yuki: { answer_length } })}
                />
              </SettingRow>
              <SettingRow name="Speak the answer aloud">
                <Toggle
                  label="Speak the answer"
                  checked={settings.ask_yuki.speak_answer}
                  onChange={(speak_answer) => void update({ ask_yuki: { speak_answer } })}
                />
              </SettingRow>
              <SettingRow name="Model" hint="Ollama models installed on this computer.">
                <select
                  className="select"
                  style={{ maxWidth: 220 }}
                  value={settings.ask_yuki.model ?? ""}
                  onChange={(e) => void update({ ask_yuki: { model: e.target.value || null } })}
                >
                  <option value="">Default</option>
                  {(health?.ollama?.models ?? []).map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </SettingRow>
            </>
          )}

          {section === "advanced" && (
            <>
              <SettingRow name="Speech model" hint={`Currently ${health?.whisper?.model ?? "unknown"} (${health?.whisper?.state ?? "unknown"}).`}>
                <span className="settings-row__hint">{health?.whisper?.loaded ? "Loaded" : "Not loaded"}</span>
              </SettingRow>
              <SettingRow name="Developer tools" hint="Shows Can-do jump and reset actions in the lesson menu.">
                <Toggle
                  label="Developer tools"
                  checked={settings.advanced.developer_tools}
                  onChange={(developer_tools) => void update({ advanced: { developer_tools } })}
                />
              </SettingRow>
              <SettingRow name="Diagnostics">
                <span style={{ display: "flex", gap: "var(--sp-2)" }}>
                  <button type="button" className="btn btn--ghost" onClick={() => void window.jtutor?.openLogs?.()}>
                    Open log folder
                  </button>
                  <button type="button" className="btn btn--ghost" onClick={() => void window.jtutor?.restartBackend?.()}>
                    Restart backend
                  </button>
                </span>
              </SettingRow>
              <p className="settings-row__hint">
                API: {api.base()} · data: {String(health?.settings?.data_dir ?? "—")}
              </p>
            </>
          )}
        </div>
      </div>
    </Dialog>
  );
}
