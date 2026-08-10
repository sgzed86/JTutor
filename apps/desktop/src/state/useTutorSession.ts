/**
 * Owns the tutor session: fetching, advancing, speaking, recording and grading.
 *
 * This is the logic that used to live inline in a 586-line `Tutor.tsx`. The
 * important behavioural rules it encodes:
 *
 *  - Sequencing is the server's. The client only calls `advance()` when the
 *    server said the step auto-advances, and never for a `kind: "help"` payload.
 *  - The step renders immediately; audio plays alongside it rather than
 *    blocking the render path.
 *  - Ask Yuki never touches the stage's busy state.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { ApiError, isAbort, toApiError } from "../api/errors";
import type { AudioJob } from "../audio/useAudioPipeline";
import { useAudioPipeline } from "../audio/useAudioPipeline";
import type { RecorderPurpose, RecordingResult } from "../audio/useRecorder";
import { useRecorder } from "../audio/useRecorder";
import type { Grade, Message, Step, TutorPayload } from "../api/types";
import type { BlockedReason, TutorPhase } from "./tutorPhase";
import { autoAdvances, expectsSpeech, phaseFor, presentationFor } from "./tutorPhase";
import type { UserSettings } from "../api/types";

export type Notice = {
  id: number;
  severity: "info" | "warning" | "error";
  message: string;
  hint?: string | null;
  action?: { label: string; run: () => void } | null;
};

let noticeId = 0;

function assistantLines(payload: TutorPayload, alreadySpoken: number): Message[] {
  const assistants = payload.messages.filter((m) => m.role === "assistant");
  return assistants.slice(alreadySpoken);
}

function jobsFor(step: Step | null | undefined, lines: Message[]): AudioJob[] {
  const jobs: AudioJob[] = lines.map((m) => ({ kind: "tts" as const, text: m.content }));
  const tracks = step?.play_audio || [];
  for (const path of tracks) jobs.push({ kind: "book", path });
  return jobs;
}

export function useTutorSession(lessonId: string, settings: UserSettings) {
  const [payload, setPayload] = useState<TutorPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [transcribing, setTranscribing] = useState(false);
  const [grading, setGrading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [lastGrade, setLastGrade] = useState<Grade | null>(null);
  const [lastRecordingUrl, setLastRecordingUrl] = useState<string | null>(null);
  const [blocked, setBlocked] = useState<{ reason: BlockedReason; message: string } | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [pendingAdvance, setPendingAdvance] = useState<{ startedAt: number; delayMs: number } | null>(null);

  const spokenCountRef = useRef(0);
  const requestRef = useRef<AbortController | null>(null);
  const askRef = useRef<AbortController | null>(null);
  const advanceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const settingsRef = useRef(settings);
  settingsRef.current = settings;

  const dismissNotice = useCallback((id: number) => {
    setNotices((current) => current.filter((n) => n.id !== id));
  }, []);

  const pushNotice = useCallback((notice: Omit<Notice, "id">) => {
    const id = ++noticeId;
    setNotices((current) => [...current.filter((n) => n.message !== notice.message), { ...notice, id }]);
    if (notice.severity !== "error") {
      setTimeout(() => setNotices((c) => c.filter((n) => n.id !== id)), 8000);
    }
    return id;
  }, []);

  const reportError = useCallback(
    (err: unknown, fallback?: string) => {
      if (isAbort(err)) return;
      const apiErr = err instanceof ApiError ? err : toApiError(err);
      if (apiErr.code === "lesson_locked") {
        setBlocked({ reason: "lesson_locked", message: apiErr.message });
        return;
      }
      pushNotice({
        severity: apiErr.severity,
        message: fallback ? `${fallback}: ${apiErr.message}` : apiErr.message,
        hint: apiErr.hint,
      });
    },
    [pushNotice],
  );

  const audio = useAudioPipeline({
    tutorVolume: settings.audio.tutor_volume,
    bookVolume: settings.audio.book_volume,
    bookRate: settings.audio.book_rate,
    outputDeviceId: settings.audio.output_device_id,
    onTtsUnavailable: () =>
      pushNotice({
        severity: "info",
        message: "Yuki has no voice right now — VOICEVOX isn't running.",
        hint: "Start VOICEVOX to hear the tutor. The lesson still works.",
      }),
  });

  // --- server calls -------------------------------------------------------

  const applyPayload = useCallback((next: TutorPayload) => {
    setPayload(next);
    if (next.grade) setLastGrade(next.grade);
    return next;
  }, []);

  const cancelInFlight = useCallback(() => {
    requestRef.current?.abort();
    requestRef.current = null;
    setTranscribing(false);
    setGrading(false);
  }, []);

  const clearPendingAdvance = useCallback(() => {
    if (advanceTimerRef.current) clearTimeout(advanceTimerRef.current);
    advanceTimerRef.current = null;
    setPendingAdvance(null);
  }, []);

  const advance = useCallback(async () => {
    clearPendingAdvance();
    audio.cancel();
    const controller = new AbortController();
    requestRef.current = controller;
    try {
      applyPayload(await api.advance(lessonId, controller.signal));
    } catch (err) {
      reportError(err, "Couldn't continue");
    } finally {
      if (requestRef.current === controller) requestRef.current = null;
    }
  }, [applyPayload, audio, clearPendingAdvance, lessonId, reportError]);

  const sendAnswer = useCallback(
    async (text: string, spoken: boolean) => {
      const controller = new AbortController();
      requestRef.current = controller;
      setGrading(true);
      try {
        applyPayload(await api.message(lessonId, text, spoken, controller.signal));
      } catch (err) {
        reportError(err, "Couldn't send your answer");
      } finally {
        setGrading(false);
        if (requestRef.current === controller) requestRef.current = null;
      }
    },
    [applyPayload, lessonId, reportError],
  );

  const ask = useCallback(
    async (text: string, spoken = false) => {
      const question = text.trim();
      if (!question) return;
      askRef.current?.abort();
      const controller = new AbortController();
      askRef.current = controller;
      setAsking(true);
      try {
        const next = await api.askTutor(lessonId, question, spoken, controller.signal);
        // A help payload echoes the current step, including its audio and
        // auto-advance flags. Merge only the conversation so the stage stays put.
        setPayload((current) =>
          current
            ? { ...current, messages: next.messages, help_messages: next.help_messages, lesson_messages: next.lesson_messages }
            : next,
        );
        if (settingsRef.current.ask_yuki.speak_answer) {
          const reply = next.help_messages.filter((m) => m.role === "assistant").slice(-1);
          if (reply.length) void audio.play(reply.map((m) => ({ kind: "tts" as const, text: m.content })));
        }
      } catch (err) {
        reportError(err, "Ask Yuki");
      } finally {
        setAsking(false);
        if (askRef.current === controller) askRef.current = null;
      }
    },
    [audio, lessonId, reportError],
  );

  const cancelAsk = useCallback(() => askRef.current?.abort(), []);

  const submitSelfCheck = useCallback(
    async (stars: number, comment: string) => {
      const canDoId = payload?.self_check?.can_do_id;
      if (!canDoId) return;
      try {
        applyPayload(await api.selfCheck(lessonId, canDoId, stars, comment));
      } catch (err) {
        reportError(err, "Couldn't save your rating");
      }
    },
    [applyPayload, lessonId, payload?.self_check?.can_do_id, reportError],
  );

  const restart = useCallback(async () => {
    audio.cancel();
    spokenCountRef.current = 0;
    try {
      applyPayload(await api.resetTutor(lessonId));
    } catch (err) {
      reportError(err, "Couldn't restart the lesson");
    }
  }, [applyPayload, audio, lessonId, reportError]);

  const jumpToCanDo = useCallback(
    async (resetProgress = false) => {
      audio.cancel();
      spokenCountRef.current = 0;
      try {
        applyPayload(await api.jumpToCanDoQuiz(lessonId, resetProgress));
      } catch (err) {
        reportError(err, "Couldn't open the Can-do check");
      }
    },
    [applyPayload, audio, lessonId, reportError],
  );

  // --- recording ----------------------------------------------------------

  const handleRecording = useCallback(
    async (result: RecordingResult) => {
      if (lastRecordingUrl) URL.revokeObjectURL(lastRecordingUrl);
      setLastRecordingUrl(URL.createObjectURL(result.blob));

      if (!result.heardSpeech || result.blob.size < 600) {
        pushNotice({
          severity: "warning",
          message: "I didn't hear anything.",
          hint: "Check your microphone in Settings → Audio, then try again.",
        });
        return;
      }

      const controller = new AbortController();
      requestRef.current = controller;
      setTranscribing(true);
      let text = "";
      try {
        const hint =
          result.purpose === "answer"
            ? payload?.step?.say_target_jp ||
              payload?.step?.expected_phrases?.[0] ||
              payload?.activity?.key_phrases?.[0] ||
              ""
            : "";
        const transcript = await api.transcribe(result.blob, "ja", controller.signal, hint);
        text = (transcript.text || "").trim();
      } catch (err) {
        reportError(err, "Speech recognition");
        return;
      } finally {
        setTranscribing(false);
        if (requestRef.current === controller) requestRef.current = null;
      }

      if (!text) {
        pushNotice({ severity: "warning", message: "I couldn't make that out — try again." });
        return;
      }
      if (result.purpose === "question") {
        await ask(text, true);
      } else {
        await sendAnswer(text, true);
      }
    },
    [ask, lastRecordingUrl, payload, pushNotice, reportError, sendAnswer],
  );

  const recorder = useRecorder({
    deviceId: settings.audio.input_device_id,
    autoStopOnSilence: settings.lessons.auto_stop_on_silence,
    silenceMs: settings.lessons.silence_ms,
    maxMs: settings.lessons.max_recording_ms,
    onResult: (result) => void handleRecording(result),
    onError: (err) => {
      setBlocked({ reason: err.reason, message: err.message });
      pushNotice({ severity: "warning", message: err.message, hint: "Settings → Audio lets you pick a device." });
    },
  });

  const startRecording = useCallback(
    (purpose: RecorderPurpose = "answer") => {
      setBlocked(null);
      audio.cancel();
      void recorder.start(purpose);
    },
    [audio, recorder],
  );

  // --- lesson lifecycle ---------------------------------------------------

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    setLoading(true);
    setBlocked(null);
    setLastGrade(null);
    spokenCountRef.current = 0;
    (async () => {
      try {
        const first = await api.startTutor(lessonId, controller.signal);
        if (cancelled) return;
        // Resuming: do not re-speak the whole backlog, only the latest line.
        const assistants = first.messages.filter((m) => m.role === "assistant").length;
        spokenCountRef.current = assistants > 1 ? assistants - 1 : 0;
        applyPayload(first);
      } catch (err) {
        if (!cancelled) reportError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
      controller.abort();
      audio.cancel();
      recorder.cancel();
      clearPendingAdvance();
    };
    // audio/recorder identities are stable enough; re-running on lessonId is the intent.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lessonId]);

  // Play new tutor lines and book audio for the current step, then honour the
  // server's auto-advance flag. The step itself is already on screen.
  useEffect(() => {
    if (!payload || payload.kind === "help") return;
    const step = payload.step;
    const newLines = assistantLines(payload, spokenCountRef.current);
    const total = payload.messages.filter((m) => m.role === "assistant").length;
    if (!newLines.length && !(step?.play_audio || []).length) return;
    spokenCountRef.current = total;

    let cancelled = false;
    const jobs = jobsFor(step, newLines);
    (async () => {
      if (jobs.length) await audio.play(jobs);
      if (cancelled) return;

      const mode = settingsRef.current.lessons.auto_advance;
      const shouldAuto =
        autoAdvances(step) &&
        !expectsSpeech(step) &&
        (mode === "after_audio" || mode === "after_audio_and_answer");

      if (shouldAuto) {
        const delay = settingsRef.current.lessons.auto_advance_delay_ms;
        setPendingAdvance({ startedAt: Date.now(), delayMs: delay });
        advanceTimerRef.current = setTimeout(() => {
          setPendingAdvance(null);
          void advance();
        }, delay);
        return;
      }
      if (expectsSpeech(step) && settingsRef.current.lessons.auto_start_recording) {
        startRecording("answer");
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [payload]);

  // Prefetch the next step's tutor line so there is no gap after the CD.
  useEffect(() => {
    const upcoming = payload?.step?.say_target_jp;
    if (upcoming) audio.prefetch([{ kind: "tts", text: upcoming }]);
  }, [audio, payload?.step?.say_target_jp]);

  const phase: TutorPhase = useMemo(
    () =>
      phaseFor({
        payload,
        loading,
        speakingLine: audio.speakingText,
        audio: audio.position,
        recordingStartedAt: recorder.recording ? recorder.startedAt : null,
        transcribing,
        grading,
        blocked,
      }),
    [audio.position, audio.speakingText, blocked, grading, loading, payload, recorder.recording, recorder.startedAt, transcribing],
  );

  const presentation = useMemo(
    () => presentationFor(phase, { micMode: settings.lessons.mic_mode, lastGrade }),
    [lastGrade, phase, settings.lessons.mic_mode],
  );

  const runPrimaryAction = useCallback(() => {
    switch (presentation.primary.id) {
      case "skip_line":
      case "skip_audio":
        audio.cancel();
        return;
      case "record":
        startRecording("answer");
        return;
      case "stop_recording":
        recorder.stop();
        return;
      case "cancel":
        cancelInFlight();
        return;
      case "retry":
        setBlocked(null);
        return;
      default:
        void advance();
    }
  }, [advance, audio, cancelInFlight, presentation.primary.id, recorder, startRecording]);

  const replayTutorLine = useCallback(() => {
    const last = payload?.lesson_messages.filter((m) => m.role === "assistant").slice(-1) ?? [];
    if (last.length) void audio.play([{ kind: "tts", text: last[0].content }]);
  }, [audio, payload?.lesson_messages]);

  const replayBookAudio = useCallback(() => {
    const tracks = payload?.step?.play_audio || [];
    if (tracks.length) void audio.play(tracks.map((path) => ({ kind: "book" as const, path })));
  }, [audio, payload?.step?.play_audio]);

  return {
    payload,
    phase,
    presentation,
    notices,
    dismissNotice,
    pushNotice,
    lastGrade,
    lastRecordingUrl,
    asking,
    pendingAdvance,
    recorder,
    audio,
    actions: {
      advance,
      runPrimaryAction,
      startRecording,
      stopRecording: recorder.stop,
      cancelRecording: recorder.cancel,
      sendAnswer,
      ask,
      cancelAsk,
      submitSelfCheck,
      restart,
      jumpToCanDo,
      replayTutorLine,
      replayBookAudio,
      cancelPendingAdvance: clearPendingAdvance,
      cancelInFlight,
    },
  };
}

export type TutorSession = ReturnType<typeof useTutorSession>;
