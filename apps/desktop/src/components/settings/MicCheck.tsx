import { useCallback, useEffect, useRef, useState } from "react";
import { SettingRow } from "../ui/controls";

/**
 * Pick an input device and confirm it actually works. Previously nothing told a
 * learner their microphone was broken until they were mid-lesson.
 */
export function MicCheck({
  deviceId,
  onSelectDevice,
}: {
  deviceId: string | null;
  onSelectDevice: (id: string | null) => void;
}) {
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [level, setLevel] = useState(0);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const stopRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    navigator.mediaDevices
      ?.enumerateDevices()
      .then((list) => setDevices(list.filter((d) => d.kind === "audioinput")))
      .catch(() => undefined);
    return () => stopRef.current?.();
  }, []);

  const startTest = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { deviceId: deviceId ? { exact: deviceId } : undefined },
      });
      const Ctx = window.AudioContext;
      const ctx = new Ctx();
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      const buffer = new Uint8Array(analyser.fftSize);
      let raf = 0;
      const tick = () => {
        analyser.getByteTimeDomainData(buffer);
        let sum = 0;
        for (let i = 0; i < buffer.length; i += 1) {
          const v = (buffer[i] - 128) / 128;
          sum += v * v;
        }
        setLevel(Math.min(1, Math.sqrt(sum / buffer.length) * 4));
        raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);
      setTesting(true);
      stopRef.current = () => {
        cancelAnimationFrame(raf);
        stream.getTracks().forEach((t) => t.stop());
        void ctx.close();
        setTesting(false);
        setLevel(0);
        stopRef.current = null;
      };
      // Refresh labels: they are only populated once permission is granted.
      const list = await navigator.mediaDevices.enumerateDevices();
      setDevices(list.filter((d) => d.kind === "audioinput"));
    } catch {
      setError("Jtutor couldn't open that microphone. Check your system privacy settings.");
    }
  }, [deviceId]);

  return (
    <>
      <SettingRow name="Microphone">
        <select
          className="select"
          style={{ maxWidth: 240 }}
          value={deviceId ?? ""}
          onChange={(e) => onSelectDevice(e.target.value || null)}
        >
          <option value="">System default</option>
          {devices.map((device) => (
            <option key={device.deviceId} value={device.deviceId}>
              {device.label || "Microphone"}
            </option>
          ))}
        </select>
      </SettingRow>
      <SettingRow name="Test it" hint="Speak and watch the meter move.">
        <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--sp-2)" }}>
          <span className="meter">
            <span className="meter__fill" style={{ width: `${Math.round(level * 100)}%` }} />
          </span>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => (testing ? stopRef.current?.() : void startTest())}
          >
            {testing ? "Stop" : "Test"}
          </button>
        </span>
      </SettingRow>
      {error && <p className="settings-row__hint">{error}</p>}
    </>
  );
}
