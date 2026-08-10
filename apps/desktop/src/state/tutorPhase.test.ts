import { describe, expect, it } from "vitest";
import type { TutorPayload } from "../api/types";
import { autoAdvances, expectsSpeech, phaseFor, presentationFor } from "./tutorPhase";

function payload(overrides: Partial<TutorPayload> = {}): TutorPayload {
  return {
    kind: "step",
    session_id: 1,
    lesson_id: "L01",
    state: "book",
    activity_id: "A1",
    activity: null,
    messages: [],
    lesson_messages: [],
    help_messages: [],
    can_dos: [],
    quiz_index: 0,
    step: { expects_speech: false, auto_advance: false },
    progress: { fraction: 0, percent: 0, phase: "book", label: "Book" },
    segments: [],
    grammar: [],
    vocab: [],
    grade: null,
    self_check: null,
    self_checks: [],
    next_lesson_id: null,
    ...overrides,
  };
}

const idle = {
  payload: payload(),
  loading: false,
  speakingLine: null,
  audio: null,
  recordingStartedAt: null,
  transcribing: false,
  grading: false,
  blocked: null,
};

describe("phaseFor", () => {
  it("is loading until the first payload arrives", () => {
    expect(phaseFor({ ...idle, payload: null, loading: true }).kind).toBe("loading");
  });

  it("prefers recording over every other signal", () => {
    const phase = phaseFor({
      ...idle,
      recordingStartedAt: 123,
      speakingLine: "おはよう",
      transcribing: true,
      grading: true,
    });
    expect(phase.kind).toBe("recording");
  });

  it("reports awaiting_speech only when the step asks for it", () => {
    expect(phaseFor(idle).kind).toBe("idle_can_continue");
    const speaking = phaseFor({
      ...idle,
      payload: payload({ step: { expects_speech: true, say_target_jp: "おはよう" } }),
    });
    expect(speaking).toEqual({ kind: "awaiting_speech", target: "おはよう" });
  });

  it("surfaces a blocked microphone instead of pretending to listen", () => {
    const phase = phaseFor({
      ...idle,
      payload: payload({ step: { expects_speech: true } }),
      blocked: { reason: "mic_unavailable", message: "No microphone found." },
    });
    expect(phase).toEqual({ kind: "blocked", reason: "mic_unavailable", message: "No microphone found." });
  });

  it("ends at lesson_complete", () => {
    const phase = phaseFor({ ...idle, payload: payload({ state: "lesson_complete", next_lesson_id: "L02" }) });
    expect(phase).toEqual({ kind: "lesson_complete", nextLessonId: "L02" });
  });

  it("opens the self-check when the server is waiting for one", () => {
    const phase = phaseFor({
      ...idle,
      payload: payload({ state: "self_check", self_check: { can_do_id: "CD_L01_01" } }),
    });
    expect(phase).toEqual({ kind: "self_check", canDoId: "CD_L01_01" });
  });
});

describe("presentationFor", () => {
  const kinds = [
    { kind: "loading" },
    { kind: "speaking", line: "x" },
    { kind: "playing_audio", index: 0, total: 2, path: "a.mp3" },
    { kind: "awaiting_speech", target: null },
    { kind: "recording", startedAt: 1 },
    { kind: "transcribing" },
    { kind: "grading" },
    { kind: "idle_can_continue" },
    { kind: "self_check", canDoId: "x" },
    { kind: "lesson_complete", nextLessonId: null },
    { kind: "blocked", reason: "mic_denied", message: "nope" },
  ] as const;

  it("gives every phase exactly one status and one primary action", () => {
    for (const phase of kinds) {
      const p = presentationFor(phase, { micMode: "hold" });
      expect(p.status).toBeTruthy();
      expect(p.primary.id).toBeTruthy();
      expect(p.primary.label).toBeTruthy();
    }
  });

  it("never claims to be listening while blocked", () => {
    const p = presentationFor({ kind: "blocked", reason: "mic_unavailable", message: "No microphone found." }, { micMode: "hold" });
    expect(p.mood).not.toBe("listening");
    expect(p.status).toBe("No microphone found.");
  });

  it("labels the mic button for the configured mode", () => {
    expect(presentationFor({ kind: "awaiting_speech", target: null }, { micMode: "hold" }).primary.label).toBe(
      "Hold to speak",
    );
    expect(presentationFor({ kind: "awaiting_speech", target: null }, { micMode: "toggle" }).primary.label).toBe(
      "Tap to speak",
    );
  });
});

describe("step flag accessors", () => {
  it("prefers the self-describing fields over the legacy aliases", () => {
    expect(expectsSpeech({ expects_speech: true, expect_speech: false })).toBe(true);
    expect(autoAdvances({ auto_advance: true, auto_advance_after_audio: false })).toBe(true);
  });

  it("falls back to the legacy aliases for older payloads", () => {
    expect(expectsSpeech({ expect_speech: true })).toBe(true);
    expect(autoAdvances({ auto_advance_after_audio: true })).toBe(true);
    expect(expectsSpeech(null)).toBe(false);
    expect(autoAdvances(undefined)).toBe(false);
  });
});
