/**
 * One audio pipeline for the whole app.
 *
 * Previously TTS chunks and book tracks each created their own `new Audio()`
 * with nothing able to pause, cancel, prefetch or measure them. This owns a
 * single AudioContext + analyser so playback is interruptible and the avatar can
 * lip-sync to the actual output level.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { isAbort } from "../api/errors";

export type AudioJob =
  | { kind: "tts"; text: string }
  | { kind: "book"; path: string };

export type PlaybackPosition = { index: number; total: number; path: string } | null;

type Options = {
  tutorVolume: number;
  bookVolume: number;
  bookRate: number;
  outputDeviceId?: string | null;
  onTtsUnavailable?: (message: string) => void;
};

type ElementWithSink = HTMLAudioElement & { setSinkId?: (id: string) => Promise<void> };

export type AudioPipeline = {
  play: (jobs: AudioJob[], opts?: { onBookStart?: (position: PlaybackPosition) => void }) => Promise<void>;
  cancel: () => void;
  replayLast: () => Promise<void>;
  prefetch: (jobs: AudioJob[]) => void;
  speakingText: string | null;
  position: PlaybackPosition;
  level: number;
  isBusy: boolean;
};

const ttsCache = new Map<string, string>();

function objectUrlFor(blob: Blob): string {
  return URL.createObjectURL(blob);
}

export function useAudioPipeline(options: Options): AudioPipeline {
  const [speakingText, setSpeakingText] = useState<string | null>(null);
  const [position, setPosition] = useState<PlaybackPosition>(null);
  const [level, setLevel] = useState(0);
  const [isBusy, setBusy] = useState(false);

  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const elementRef = useRef<ElementWithSink | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const gainRef = useRef<GainNode | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const rafRef = useRef<number | null>(null);
  const lastJobsRef = useRef<AudioJob[]>([]);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const ensureGraph = useCallback(() => {
    if (!elementRef.current) {
      const el = new Audio() as ElementWithSink;
      el.preload = "auto";
      el.crossOrigin = "anonymous";
      elementRef.current = el;
    }
    if (!ctxRef.current) {
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!Ctx) return null;
      const ctx = new Ctx();
      const source = ctx.createMediaElementSource(elementRef.current);
      const gain = ctx.createGain();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.7;
      source.connect(gain);
      gain.connect(analyser);
      analyser.connect(ctx.destination);
      ctxRef.current = ctx;
      sourceRef.current = source;
      gainRef.current = gain;
      analyserRef.current = analyser;
    }
    if (ctxRef.current.state === "suspended") void ctxRef.current.resume();
    return ctxRef.current;
  }, []);

  const startMeter = useCallback(() => {
    if (rafRef.current !== null) return;
    const buffer = new Uint8Array(256);
    const tick = () => {
      const analyser = analyserRef.current;
      if (!analyser) {
        rafRef.current = null;
        return;
      }
      analyser.getByteTimeDomainData(buffer);
      let sum = 0;
      for (let i = 0; i < buffer.length; i += 1) {
        const v = (buffer[i] - 128) / 128;
        sum += v * v;
      }
      setLevel(Math.min(1, Math.sqrt(sum / buffer.length) * 3));
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const stopMeter = useCallback(() => {
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    setLevel(0);
  }, []);

  const playUrl = useCallback(
    (url: string, volume: number, rate: number, signal: AbortSignal) =>
      new Promise<void>((resolve, reject) => {
        ensureGraph();
        const el = elementRef.current;
        if (!el) return resolve();
        if (gainRef.current) gainRef.current.gain.value = volume;
        el.playbackRate = rate;

        const deviceId = optionsRef.current.outputDeviceId;
        if (deviceId && typeof el.setSinkId === "function") {
          el.setSinkId(deviceId).catch(() => undefined);
        }

        const cleanup = () => {
          el.onended = null;
          el.onerror = null;
          signal.removeEventListener("abort", onAbort);
        };
        const onAbort = () => {
          cleanup();
          el.pause();
          resolve();
        };
        el.onended = () => {
          cleanup();
          resolve();
        };
        el.onerror = () => {
          cleanup();
          reject(new Error("Playback failed"));
        };
        signal.addEventListener("abort", onAbort, { once: true });

        el.src = url;
        startMeter();
        el.play().catch((err) => {
          cleanup();
          // Autoplay restrictions or a missing file: not worth blocking the lesson.
          reject(err);
        });
      }),
    [ensureGraph, startMeter],
  );

  const ttsUrl = useCallback(async (text: string, signal: AbortSignal): Promise<string | null> => {
    const cached = ttsCache.get(text);
    if (cached) return cached;
    try {
      const blob = await api.speak(text, signal);
      const url = objectUrlFor(blob);
      ttsCache.set(text, url);
      return url;
    } catch (err) {
      if (!isAbort(err)) {
        optionsRef.current.onTtsUnavailable?.(err instanceof Error ? err.message : String(err));
      }
      return null;
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    const el = elementRef.current;
    if (el) {
      el.pause();
      el.removeAttribute("src");
    }
    stopMeter();
    setSpeakingText(null);
    setPosition(null);
    setBusy(false);
  }, [stopMeter]);

  const play = useCallback(
    async (jobs: AudioJob[], opts?: { onBookStart?: (position: PlaybackPosition) => void }) => {
      cancel();
      if (!jobs.length) return;
      lastJobsRef.current = jobs;
      const controller = new AbortController();
      abortRef.current = controller;
      setBusy(true);

      const bookJobs = jobs.filter((j) => j.kind === "book");
      let bookIndex = 0;

      try {
        for (const job of jobs) {
          if (controller.signal.aborted) break;
          if (job.kind === "tts") {
            setSpeakingText(job.text);
            const url = await ttsUrl(job.text, controller.signal);
            if (!url || controller.signal.aborted) {
              setSpeakingText(null);
              continue;
            }
            await playUrl(url, optionsRef.current.tutorVolume, 1, controller.signal).catch(() => undefined);
            setSpeakingText(null);
          } else {
            const pos = { index: bookIndex, total: bookJobs.length, path: job.path };
            bookIndex += 1;
            setPosition(pos);
            opts?.onBookStart?.(pos);
            await playUrl(
              api.audioUrl(job.path),
              optionsRef.current.bookVolume,
              optionsRef.current.bookRate,
              controller.signal,
            ).catch(() => undefined);
            setPosition(null);
          }
        }
      } finally {
        stopMeter();
        setSpeakingText(null);
        setPosition(null);
        setBusy(false);
        if (abortRef.current === controller) abortRef.current = null;
      }
    },
    [cancel, playUrl, stopMeter, ttsUrl],
  );

  const prefetch = useCallback(
    (jobs: AudioJob[]) => {
      for (const job of jobs) {
        if (job.kind === "tts" && !ttsCache.has(job.text)) {
          void ttsUrl(job.text, new AbortController().signal);
        }
        if (job.kind === "book") {
          const img = new Audio();
          img.preload = "auto";
          img.src = api.audioUrl(job.path);
        }
      }
    },
    [ttsUrl],
  );

  const replayLast = useCallback(async () => {
    if (lastJobsRef.current.length) await play(lastJobsRef.current);
  }, [play]);

  useEffect(() => () => {
    abortRef.current?.abort();
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    void ctxRef.current?.close();
  }, []);

  return useMemo(
    () => ({ play, cancel, replayLast, prefetch, speakingText, position, level, isBusy }),
    [play, cancel, replayLast, prefetch, speakingText, position, level, isBusy],
  );
}
