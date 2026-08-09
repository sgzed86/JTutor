import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Step, TutorPayload } from "../../api/types";
import { TutorStage } from "./TutorStage";

function payload(step: Step, extra: Partial<TutorPayload> = {}): TutorPayload {
  return {
    kind: "step",
    session_id: 1,
    lesson_id: "L01",
    state: "book",
    activity_id: "A1",
    activity: { id: "A1", key_phrases: ["おはよう"] },
    messages: [{ role: "assistant", content: "聞いて、言いましょう。", hint_en: "Listen and repeat" }],
    lesson_messages: [{ role: "assistant", content: "聞いて、言いましょう。", hint_en: "Listen and repeat" }],
    help_messages: [],
    can_dos: [],
    quiz_index: 0,
    step,
    progress: { fraction: 0.1, percent: 10, phase: "book", label: "Book" },
    segments: [],
    grammar: [],
    vocab: [],
    grade: null,
    self_check: null,
    self_checks: [],
    next_lesson_id: null,
    ...extra,
  };
}

const noop = () => undefined;

function renderStage(step: Step, overrides: Partial<Parameters<typeof TutorStage>[0]> = {}) {
  return render(
    <TutorStage
      payload={payload(step)}
      mood="idle"
      level={0}
      reduceMotion
      lastGrade={null}
      lastRecordingUrl={null}
      onReplayTutor={noop}
      onReplayBook={noop}
      onPlayTarget={noop}
      {...overrides}
    />,
  );
}

describe("TutorStage", () => {
  it("shows the phrase to say when the step wants speech", () => {
    renderStage({ book_substep: "repeat", expects_speech: true, say_target_jp: "おはよう" });
    expect(screen.getByText("おはよう")).toBeInTheDocument();
    expect(screen.getByText("Repeat aloud")).toBeInTheDocument();
  });

  it("renders the activity progress segments from the server", () => {
    renderStage({
      book_substep: "repeat",
      substeps: ["listen", "repeat", "repeat"],
      substep_index: 1,
      activity_index: 0,
      activity_total: 3,
    });
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "2");
    expect(bar).toHaveAttribute("aria-valuemax", "3");
  });

  it("offers a replay control for the tutor line", () => {
    const onReplayTutor = vi.fn();
    renderStage({ book_substep: "listen" }, { onReplayTutor });
    screen.getByRole("button", { name: /hear again/i }).click();
    expect(onReplayTutor).toHaveBeenCalled();
  });

  it("shows the transcript and a diff when an answer fails", () => {
    renderStage(
      { book_substep: "repeat", expects_speech: true, say_target_jp: "おはよう" },
      {
        lastGrade: {
          passed: false,
          score: 42,
          transcript: "おは",
          best_match: "おはよう",
          diff: [
            { text: "おは", match: true },
            { text: "よう", match: false },
          ],
          feedback_en: "Close — try again.",
        },
      },
    );
    expect(screen.getByText("42%")).toBeInTheDocument();
    expect(screen.getByText(/Close — try again/)).toBeInTheDocument();
    expect(screen.getByText("よう")).toBeInTheDocument();
  });

  it("keeps a single instruction line rather than repeating it", () => {
    renderStage({ book_substep: "listen", instruction_en: "Listen to the book CD." });
    expect(screen.getAllByText("Listen to the book CD.")).toHaveLength(1);
  });
});
