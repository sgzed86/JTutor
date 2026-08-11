import { describe, expect, it } from "vitest";
import type { Step, TutorPayload } from "../api/types";
import { buildTutorStageModel } from "./tutorDisplay";

function payload(step: Step, extra: Partial<TutorPayload> = {}): TutorPayload {
  return {
    kind: "step",
    session_id: 1,
    lesson_id: "L01",
    state: "book",
    activity_id: "A1",
    activity: { id: "A1", key_phrases: ["おはよう", "おはようございます"] },
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

describe("buildTutorStageModel", () => {
  it("uses the server's activity position rather than guessing", () => {
    const model = buildTutorStageModel(
      payload({ book_substep: "listen", activity_index: 6, activity_total: 28, substeps: ["listen", "repeat"], substep_index: 0 }),
    );
    expect(model.activityLabel).toBe("Activity 7 of 28");
    expect(model.substeps).toEqual(["listen", "repeat"]);
    expect(model.substepIndex).toBe(0);
  });

  it("shows a preview card on the listen sub-step", () => {
    const model = buildTutorStageModel(payload({ book_substep: "listen", say_target_jp: "おはよう" }));
    expect(model.focus).toBe("listen-preview");
    expect(model.sayLabel).toBe("After the CD, you will say");
  });

  it("shows the say card when the step wants speech", () => {
    const model = buildTutorStageModel(
      payload({ book_substep: "repeat", expects_speech: true, say_target_jp: "おはよう" }),
    );
    expect(model.focus).toBe("say");
    expect(model.sayTargetJp).toBe("おはよう");
  });

  it("marks the learner role-play line orange", () => {
    const model = buildTutorStageModel(
      payload({
        book_substep: "learner",
        expects_speech: true,
        dialog_line_jp: "はじめまして",
        book_line_color: "orange",
      }),
    );
    expect(model.lineColor).toBe("orange");
    expect(model.sayTargetJp).toBe("はじめまして");
    expect(model.sayLabel).toContain("orange");
  });

  it("marks the swapped learner turn yellow (student takes partner line)", () => {
    const model = buildTutorStageModel(
      payload({
        book_substep: "swap_learner",
        expects_speech: true,
        dialog_line_jp: "ミロさんは何歳ですか",
        say_target_jp: "ミロさんは何歳ですか",
        book_line_color: "yellow",
      }),
    );
    expect(model.lineColor).toBe("yellow");
    expect(model.sayLabel).toContain("yellow");
    expect(model.focus).toBe("say");
  });

  it("does not show a say card while Yuki speaks the partner line", () => {
    const model = buildTutorStageModel(
      payload({
        book_substep: "partner",
        expects_speech: false,
        dialog_line_jp: "こんにちは",
        book_line_color: "yellow",
      }),
    );
    expect(model.focus).toBe("none");
    expect(model.lineColor).toBe("yellow");
  });

  it("marks Yuki orange on the swapped partner turn", () => {
    const model = buildTutorStageModel(
      payload({
        book_substep: "swap_partner",
        expects_speech: false,
        dialog_line_jp: "25歳です",
        book_line_color: "orange",
      }),
    );
    expect(model.focus).toBe("none");
    expect(model.lineColor).toBe("orange");
  });

  it("renders a shadow card for shadowing", () => {
    const model = buildTutorStageModel(payload({ book_substep: "shadow" }));
    expect(model.focus).toBe("shadow");
  });

  it("labels segments only when there is more than one", () => {
    const single = buildTutorStageModel(payload({ segment: { index: 0, total: 1, title_en: "Greetings" } }));
    expect(single.segmentLabel).toBeNull();
    const multi = buildTutorStageModel(payload({ segment: { index: 1, total: 4, title_en: "Greetings" } }));
    expect(multi.segmentLabel).toBe("Part 2 of 4 · Greetings");
  });

  it("always produces exactly one instruction string", () => {
    const model = buildTutorStageModel(payload({ book_substep: "repeat", expects_speech: true }));
    expect(typeof model.instructionEn).toBe("string");
  });

  it("surfaces the current book page for the learner", () => {
    const model = buildTutorStageModel(
      payload({ book_substep: "listen" }, { book_page: 101, pdf_pages: [101, 123] }),
    );
    expect(model.bookPageLabel).toBe("Book p. 101");
  });

  it("shows grammar blanks without leaking the answer", () => {
    const model = buildTutorStageModel(
      payload(
        {
          book_substep: "grammar_fill",
          expects_text: true,
          facilitate: true,
          grammar_cue_jp: "バトさん，ミロさん",
          blank_prompt_jp: "紹介します。こちら、＿。",
          blank_count: 1,
          blank_index: 0,
          blank_total: 2,
          grammar_pattern_en: "A and B (と)",
          expected_phrases: ["紹介します。こちら、バトさんとミロさんです。"],
          say_target_jp: null,
          instruction_en: "Listen to Yuki, then type the blank with と.",
        },
        { state: "grammar" },
      ),
    );
    expect(model.focus).toBe("fill");
    expect(model.sayTargetJp).toBeNull();
    expect(model.sayAlternates).toEqual([]);
    expect(model.blankPromptJp).toBe("紹介します。こちら、＿。");
    expect(model.grammarCueJp).toBe("バトさん，ミロさん");
    expect(model.sayLabel).toContain("Grammar blank");
  });
});
