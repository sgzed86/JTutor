/**
 * One recorder for both answers and questions.
 *
 * Replaces two near-identical MediaRecorder flows (and the `recordingModeRef`
 * guard that existed to stop them interfering) and adds everything the old
 * push-to-talk had none of: a live level, an elapsed timer, silence detection
 * and a real "I didn't hear anything" verdict instead of `blob.size < 800`.
 */

import { useCallback, useEffect, useRef, useState } from "react";

export type RecorderPurpose = "answer" | "question";

export type RecordingResult = {
  blob: Blob;
  durationMs: number;
  purpose: RecorderPurpose;
  heardSpeech: boolean;
  peakLevel: number;
};

export type RecorderError =
  | { reason: "mic_unavailable"; message: string }
  | { reason: "mic_denied"; message: string };

type Options = {
  deviceId?: string | null;
  autoStopOnSilence: boolean;
  silenceMs: number;
  maxMs: number;
  onResult: (result: RecordingResult) => void;
  onError: (error: RecorderError) => void;
};

const CALIBRATION_MS = 400;
const ONSET_MS = 150;
const WAVE_BARS = 48;

export type Recorder = {
  start: (purpose: RecorderPurpose) => Promise<void>;
  stop: () => void;
  cancel: () => void;
  recording: boolean;
  purpose: RecorderPurpose | null;
  startedAt: number | null;
  level: number;
  waveform: Float32Array;
  heardSpeech: boolean;
};

export function useRecorder(options: Options): Recorder {
  const [recording, setRecording] = useState(false);
  const [purpose, setPurpose] = useState<RecorderPurpose | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [level, setLevel] = useState(0);
  const [heardSpeech, setHeardSpeech] = useState(false);

  const waveformRef = useRef(new Float32Array(WAVE_BARS));
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const cancelledRef = useRef(false);
  const purposeRef = useRef<RecorderPurpose | null>(null);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const stateRef = useRef({
    noiseFloor: 0.02,
    calibrating: true,
    calibrationSum: 0,
    calibrationCount: 0,
    onsetAt: 0 as number,
    lastLoudAt: 0 as number,
    peak: 0,
    startTime: 0,
    heard: false,
  });

  const teardown = useCallback(() => {
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    void ctxRef.current?.close().catch(() => undefined);
    ctxRef.current = null;
    analyserRef.current = null;
    recorderRef.current = null;
    waveformRef.current = new Float32Array(WAVE_BARS);
    setRecording(false);
    setPurpose(null);
    setStartedAt(null);
    setLevel(0);
  }, []);

  const stop = useCallback(() => {
    const rec = recorderRef.current;
    if (rec && rec.state !== "inactive") rec.stop();
  }, []);

  const cancel = useCallback(() => {
    cancelledRef.current = true;
    stop();
    teardown();
  }, [stop, teardown]);

  const monitor = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const buffer = new Uint8Array(analyser.fftSize);
    const s = stateRef.current;

    const tick = () => {
      if (!analyserRef.current) return;
      analyser.getByteTimeDomainData(buffer);
      let sum = 0;
      for (let i = 0; i < buffer.length; i += 1) {
        const v = (buffer[i] - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / buffer.length);
      const now = performance.now();
      const elapsed = now - s.startTime;

      if (s.calibrating) {
        s.calibrationSum += rms;
        s.calibrationCount += 1;
        if (elapsed >= CALIBRATION_MS) {
          s.calibrating = false;
          const mean = s.calibrationSum / Math.max(1, s.calibrationCount);
          // Threshold sits above the measured room noise, with a sane floor.
          s.noiseFloor = Math.max(0.012, mean * 2.2);
        }
      } else {
        const loud = rms > s.noiseFloor;
        if (loud) {
          s.lastLoudAt = now;
          if (!s.onsetAt) s.onsetAt = now;
          if (s.onsetAt && now - s.onsetAt >= ONSET_MS && !s.heard) {
            s.heard = true;
            setHeardSpeech(true);
          }
        } else if (s.onsetAt && !s.heard && now - s.onsetAt > ONSET_MS) {
          s.onsetAt = 0;
        }

        const opts = optionsRef.current;
        if (s.heard && opts.autoStopOnSilence && now - s.lastLoudAt > opts.silenceMs) {
          stop();
          return;
        }
        if (elapsed > opts.maxMs) {
          stop();
          return;
        }
      }

      s.peak = Math.max(s.peak, rms);
      const scaled = Math.min(1, rms * 4);
      setLevel(scaled);
      const next = waveformRef.current;
      next.copyWithin(0, 1);
      next[next.length - 1] = scaled;

      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, [stop]);

  const start = useCallback(
    async (nextPurpose: RecorderPurpose) => {
      if (recorderRef.current) return;
      cancelledRef.current = false;
      purposeRef.current = nextPurpose;

      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            deviceId: optionsRef.current.deviceId ? { exact: optionsRef.current.deviceId } : undefined,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            channelCount: 1,
          },
        });
      } catch (err) {
        const name = err instanceof DOMException ? err.name : "";
        const denied = name === "NotAllowedError" || name === "SecurityError";
        optionsRef.current.onError({
          reason: denied ? "mic_denied" : "mic_unavailable",
          message: denied
            ? "Jtutor needs permission to use your microphone."
            : "No microphone was found. Pick one in Settings → Audio.",
        });
        return;
      }

      streamRef.current = stream;
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new Ctx();
      ctxRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.5;
      source.connect(analyser);
      analyserRef.current = analyser;

      stateRef.current = {
        noiseFloor: 0.02,
        calibrating: true,
        calibrationSum: 0,
        calibrationCount: 0,
        onsetAt: 0,
        lastLoudAt: performance.now(),
        peak: 0,
        startTime: performance.now(),
        heard: false,
      };
      setHeardSpeech(false);
      waveformRef.current = new Float32Array(WAVE_BARS);

      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const s = stateRef.current;
        const durationMs = performance.now() - s.startTime;
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const wasCancelled = cancelledRef.current;
        const result: RecordingResult = {
          blob,
          durationMs,
          purpose: purposeRef.current || "answer",
          heardSpeech: s.heard,
          peakLevel: s.peak,
        };
        teardown();
        if (!wasCancelled) optionsRef.current.onResult(result);
      };

      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
      setPurpose(nextPurpose);
      setStartedAt(Date.now());
      monitor();
    },
    [monitor, teardown],
  );

  useEffect(() => () => cancel(), [cancel]);

  return {
    start,
    stop,
    cancel,
    recording,
    purpose,
    startedAt,
    level,
    waveform: waveformRef.current,
    heardSpeech,
  };
}
