/**
 * One value describing what the tutor is doing right now.
 *
 * This replaces nine independent booleans and refs (`busy`, `recording`,
 * `speaking`, `asking`, `status`, `speakingRef`, `handlingRef`,
 * `recordingModeRef`, `step.expect_speech`) that could — and did — disagree,
 * producing a screen that said "Listening to you…" next to a red "microphone
 * not found" banner.
 *
 * The phase is derived from the server payload plus local I/O state. It never
 * decides what the next lesson step is; sequencing stays on the server.
 */

import type { Grade, Step, TutorPayload } from "../api/types";

export type BlockedReason =
  | "mic_unavailable"
  | "mic_denied"
  | "tts_unavailable"
  | "stt_unavailable"
  | "llm_unavailable"
  | "audio_missing"
  | "backend_unreachable"
  | "lesson_locked";

export type TutorPhase =
  | { kind: "loading" }
  | { kind: "speaking"; line: string }
  | { kind: "playing_audio"; index: number; total: number; path: string }
  | { kind: "awaiting_speech"; target: string | null }
  | { kind: "awaiting_text"; prompt: string | null; blankCount: number }
  | { kind: "recording"; startedAt: number }
  | { kind: "transcribing" }
  | { kind: "grading" }
  | { kind: "idle_can_continue" }
  | { kind: "self_check"; canDoId: string }
  | { kind: "lesson_complete"; nextLessonId: string | null }
  | { kind: "blocked"; reason: BlockedReason; message: string };

export type AvatarMood = "idle" | "speaking" | "listening" | "thinking" | "celebrating" | "encouraging";

export type PrimaryAction =
  | { id: "skip_line"; label: "Skip line" }
  | { id: "skip_audio"; label: "Skip audio" }
  | { id: "record"; label: string }
  | { id: "stop_recording"; label: "Stop" }
  | { id: "submit_text"; label: "Check answers" }
  | { id: "cancel"; label: "Cancel" }
  | { id: "next"; label: "Next" }
  | { id: "rate"; label: "Rate yourself" }
  | { id: "next_lesson"; label: string }
  | { id: "retry"; label: "Retry" };

export type PhasePresentation = {
  mood: AvatarMood;
  status: string;
  /** Exactly one primary action, always in the same place. */
  primary: PrimaryAction;
  busy: boolean;
  /** True only while a request that owns the stage is in flight. */
  showSpinner: boolean;
};

export function phaseFor(input: {
  payload: TutorPayload | null;
  loading: boolean;
  speakingLine: string | null;
  audio: { index: number; total: number; path: string } | null;
  recordingStartedAt: number | null;
  transcribing: boolean;
  grading: boolean;
  blocked: { reason: BlockedReason; message: string } | null;
}): TutorPhase {
  const { payload, loading, speakingLine, audio, recordingStartedAt, transcribing, grading, blocked } = input;

  if (loading && !payload) return { kind: "loading" };
  if (blocked) return { kind: "blocked", reason: blocked.reason, message: blocked.message };
  if (recordingStartedAt !== null) return { kind: "recording", startedAt: recordingStartedAt };
  if (transcribing) return { kind: "transcribing" };
  if (grading) return { kind: "grading" };
  if (speakingLine) return { kind: "speaking", line: speakingLine };
  if (audio) return { kind: "playing_audio", ...audio };

  if (!payload) return { kind: "loading" };
  if (payload.state === "lesson_complete") {
    return { kind: "lesson_complete", nextLessonId: payload.next_lesson_id };
  }
  if (payload.state === "self_check" && payload.self_check) {
    return { kind: "self_check", canDoId: payload.self_check.can_do_id };
  }
  if (expectsSpeech(payload.step)) {
    return { kind: "awaiting_speech", target: payload.step?.say_target_jp ?? null };
  }
  if (expectsText(payload.step)) {
    return {
      kind: "awaiting_text",
      prompt: payload.step?.blank_prompt_jp ?? null,
      blankCount: payload.step?.blank_count ?? 1,
    };
  }
  return { kind: "idle_can_continue" };
}

/** Reads the self-describing field, falling back to the legacy alias. */
export function expectsSpeech(step: Step | null | undefined): boolean {
  if (!step) return false;
  return Boolean(step.expects_speech ?? step.expect_speech);
}

export function expectsText(step: Step | null | undefined): boolean {
  if (!step) return false;
  if (Boolean(step.expects_text) || Boolean(step.expects_notes)) return true;
  return ["fill", "choose", "note", "read_check", "kanji_type"].includes(step.book_substep || "");
}

export function autoAdvances(step: Step | null | undefined): boolean {
  if (!step) return false;
  return Boolean(step.auto_advance ?? step.auto_advance_after_audio);
}

export function presentationFor(
  phase: TutorPhase,
  opts: { micMode: "hold" | "toggle"; lastGrade?: Grade | null; retryChoicePending?: boolean },
): PhasePresentation {
  switch (phase.kind) {
    case "loading":
      return { mood: "idle", status: "Opening the lesson…", primary: { id: "next", label: "Next" }, busy: true, showSpinner: true };
    case "speaking":
      return { mood: "speaking", status: "Yuki is speaking", primary: { id: "skip_line", label: "Skip line" }, busy: false, showSpinner: false };
    case "playing_audio":
      return {
        mood: "idle",
        status: phase.total > 1 ? `Book audio ${phase.index + 1} of ${phase.total}` : "Book audio",
        primary: { id: "skip_audio", label: "Skip audio" },
        busy: false,
        showSpinner: false,
      };
    case "awaiting_speech":
      if (opts.retryChoicePending) {
        return {
          mood: "encouraging",
          status: "What next?",
          primary: { id: "record", label: "Try again" },
          busy: false,
          showSpinner: false,
        };
      }
      return {
        mood: "listening",
        status: "Your turn",
        primary: { id: "record", label: opts.micMode === "hold" ? "Hold to speak" : "Tap to speak" },
        busy: false,
        showSpinner: false,
      };
    case "awaiting_text":
      return {
        mood: "listening",
        status: "Fill in the blanks",
        primary: { id: "submit_text", label: "Check answers" },
        busy: false,
        showSpinner: false,
      };
    case "recording":
      return { mood: "listening", status: "Listening…", primary: { id: "stop_recording", label: "Stop" }, busy: false, showSpinner: false };
    case "transcribing":
      return { mood: "thinking", status: "Hearing you…", primary: { id: "cancel", label: "Cancel" }, busy: true, showSpinner: true };
    case "grading":
      return { mood: "thinking", status: "Checking…", primary: { id: "cancel", label: "Cancel" }, busy: true, showSpinner: true };
    case "self_check":
      return { mood: "idle", status: "How did that go?", primary: { id: "rate", label: "Rate yourself" }, busy: false, showSpinner: false };
    case "lesson_complete":
      return {
        mood: "celebrating",
        status: "Lesson complete",
        primary: phase.nextLessonId
          ? { id: "next_lesson", label: `Start ${phase.nextLessonId}` }
          : { id: "next", label: "Next" },
        busy: false,
        showSpinner: false,
      };
    case "blocked":
      return { mood: "encouraging", status: phase.message, primary: { id: "retry", label: "Retry" }, busy: false, showSpinner: false };
    case "idle_can_continue":
    default:
      return {
        mood: opts.lastGrade?.passed ? "celebrating" : "idle",
        status: "Ready when you are",
        primary: { id: "next", label: "Next" },
        busy: false,
        showSpinner: false,
      };
  }
}
