/** Presentation model for the tutor stage: what to show, never what to do next. */

import type { Message, Step, TutorPayload } from "../api/types";
import { PHASE_LABEL, modeInfo, substepLabel } from "./stepLabels";

export type TutorLineColor = "yellow" | "orange" | null;
export type FocusVariant = "none" | "say" | "listen-preview" | "shadow" | "picture";

export type TutorStageModel = {
  activityLabel: string;
  stepLabel: string;
  segmentLabel: string | null;
  instructionEn: string;
  modeTitle: string;
  modeDescription: string;
  modeIcon: string;
  tutorBubbleJp: string;
  tutorBubbleEn: string;
  focus: FocusVariant;
  sayLabel: string;
  sayTargetJp: string | null;
  sayAlternates: string[];
  lineColor: TutorLineColor;
  pictureHint: string | null;
  substeps: string[];
  substepIndex: number | null;
};

function lastAssistant(messages: Message[], pick: (m: Message) => string | undefined): string {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const m = messages[i];
    if (m.role !== "assistant" || m.step?.help) continue;
    const value = pick(m);
    if (value) return value;
  }
  return "";
}

export function buildTutorStageModel(payload: TutorPayload): TutorStageModel {
  const step: Step = payload.step ?? {};
  const activity = payload.activity;
  const messages = payload.lesson_messages?.length ? payload.lesson_messages : payload.messages;
  const state = payload.state;
  const substep = step.book_substep ?? null;
  const phrases = activity?.key_phrases ?? [];

  let activityLabel = PHASE_LABEL[state] ?? "Lesson";
  if (state === "book" && step.activity_index != null && step.activity_total) {
    activityLabel = `Activity ${step.activity_index + 1} of ${step.activity_total}`;
  } else if (state === "grammar" && step.grammar_total) {
    activityLabel = `Grammar ${(step.grammar_index ?? 0) + 1} of ${step.grammar_total}`;
  } else if (state === "can_do_quiz") {
    activityLabel = `Can-do ${payload.quiz_index + 1} of ${payload.can_dos.length}`;
  }

  const mode = step.book_mode ?? activity?.book_mode ?? (state === "intro_chat" ? "intro_chat" : undefined);
  const info = modeInfo(mode);
  const stepLabel = step.substep_label_en ?? substepLabel(substep) ?? PHASE_LABEL[state] ?? "";

  const segment = step.segment;
  const segmentLabel =
    segment && segment.total > 1
      ? `Part ${segment.index + 1} of ${segment.total}${segment.title_en ? ` · ${segment.title_en}` : ""}`
      : null;

  const hintEn = payload.hint_en || lastAssistant(messages, (m) => m.hint_en) || "";
  const tutorBubbleJp =
    step.partner_jp ||
    (substep === "partner" || substep === "swap_partner" ? step.dialog_line_jp : "") ||
    lastAssistant(messages, (m) => m.content) ||
    "…";

  let instructionEn = step.instruction_en || hintEn || "";
  let sayTargetJp: string | null = step.say_target_jp ?? null;
  let sayAlternates: string[] = step.say_alternates_jp ?? step.expected_phrases ?? [];
  let lineColor: TutorLineColor = step.book_line_color ?? null;
  let sayLabel = "Say this";
  let focus: FocusVariant = "none";
  const pictureHint = step.picture_hint_en ?? activity?.picture_hint_en ?? null;
  let tutorBubbleEn = hintEn;

  const expects = Boolean(step.expects_speech ?? step.expect_speech);

  if (!sayTargetJp && phrases.length && (substep === "repeat" || substep === "select" || substep === "reply")) {
    sayTargetJp = phrases[0];
    if (!sayAlternates.length) sayAlternates = phrases.slice(1, 4);
  }
  if (!sayTargetJp && step.dialog_line_jp && expects) {
    sayTargetJp = step.dialog_line_jp;
    lineColor = lineColor ?? "orange";
  }

  if (state === "lesson_intro") {
    instructionEn = "Yuki will walk you through this lesson in book order.";
  } else if (substep === "shadow") {
    focus = "shadow";
    instructionEn = instructionEn || "Shadow now — speak quietly along with the CD. Not graded.";
  } else if (substep === "listen") {
    focus = sayTargetJp ? "listen-preview" : pictureHint ? "picture" : "none";
    sayLabel = sayTargetJp ? "After the CD, you will say" : "While you listen";
    instructionEn = instructionEn || step.up_next_en || "Listen to the book CD.";
    tutorBubbleEn = step.up_next_en ?? "";
  } else if (state === "intro_chat") {
    focus = "none";
    instructionEn = instructionEn || "Warm-up — answer freely in any language.";
  } else if (state === "grammar") {
    focus = "none";
    instructionEn = step.instruction_en || instructionEn || "Say an example aloud, or continue.";
  } else if (expects) {
    focus = sayTargetJp || sayAlternates.length ? "say" : "none";
    if (substep === "select") {
      sayLabel = "Say the phrase";
      instructionEn = instructionEn || pictureHint || "Match the picture in your book.";
    } else if (substep === "learner" || substep === "swap_learner") {
      sayLabel = "Your line (orange in the book)";
      lineColor = "orange";
    } else if (substep === "reply") {
      sayLabel = "Your reply";
      tutorBubbleEn = pictureHint || instructionEn;
    } else if (substep === "free_answer") {
      focus = "none";
      sayLabel = "Your answer";
    } else {
      sayLabel = "Repeat aloud";
    }
  } else if (substep === "partner" || substep === "swap_partner") {
    focus = "none";
    lineColor = "yellow";
    instructionEn = instructionEn || "Yuki speaks the partner line (yellow in the book).";
  }

  // One owner per message: the instruction band says what to do, so the bubble
  // gloss must add something rather than repeat it.
  if (tutorBubbleEn.trim() === instructionEn.trim()) tutorBubbleEn = "";

  return {
    activityLabel,
    stepLabel,
    segmentLabel,
    instructionEn,
    modeTitle: info.title,
    modeDescription: info.description,
    modeIcon: info.icon,
    tutorBubbleJp,
    tutorBubbleEn,
    focus,
    sayLabel,
    sayTargetJp,
    sayAlternates,
    lineColor,
    pictureHint,
    substeps: step.substeps ?? [],
    substepIndex: step.substep_index ?? null,
  };
}
