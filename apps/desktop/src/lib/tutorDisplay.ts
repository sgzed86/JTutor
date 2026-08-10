/** Presentation model for the tutor stage: what to show, never what to do next. */

import type { Message, Step, TutorPayload } from "../api/types";
import { PHASE_LABEL, modeInfo, substepLabel } from "./stepLabels";

export type TutorLineColor = "yellow" | "orange" | null;
export type FocusVariant =
  | "none"
  | "say"
  | "listen-preview"
  | "shadow"
  | "picture"
  | "fill"
  | "choose"
  | "note"
  | "passage"
  | "kanji_study"
  | "kanji_type";

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
  blankPromptJp: string | null;
  blankCount: number;
  blankIndex: number | null;
  blankTotal: number | null;
  choices: { id: string; label_jp?: string | null; label_en?: string | null }[];
  chooseMulti: boolean;
  glossEn: string | null;
  passageJp: string | null;
  passageEn: string | null;
  kanjiItems: { kanji: string; reading?: string | null; gloss_en?: string | null }[];
  kanjiPrompt: {
    kanji?: string | null;
    reading?: string | null;
    gloss_en?: string | null;
    index?: number | null;
    total?: number | null;
  } | null;
  substeps: string[];
  substepIndex: number | null;
  bookPageLabel: string | null;
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
  const blankPromptJp = step.blank_prompt_jp ?? null;
  const blankCount = Math.max(step.blank_count ?? 1, 1);
  const choices = step.choices ?? [];
  const chooseMulti = Boolean(step.choose_multi);
  const glossEn = step.gloss_en ?? null;
  const passageJp = step.passage_jp ?? null;
  const passageEn = step.passage_en ?? step.culture_notes_en ?? null;
  const kanjiItems = (step.kanji_items ?? [])
    .filter((it): it is { kanji: string; reading?: string | null; gloss_en?: string | null } => Boolean(it?.kanji))
    .map((it) => ({ kanji: it.kanji as string, reading: it.reading, gloss_en: it.gloss_en }));
  const kanjiPrompt = step.kanji_prompt ?? null;

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
    if (mode === "listen_fill" || mode === "listen_choose" || mode === "note_take") {
      focus = "none";
      instructionEn = instructionEn || step.up_next_en || "Listen to the book CD.";
    } else {
      focus = sayTargetJp ? "listen-preview" : pictureHint ? "picture" : "none";
      sayLabel = sayTargetJp ? "After the CD, you will say" : "While you listen";
      instructionEn = instructionEn || step.up_next_en || "Listen to the book CD.";
    }
    tutorBubbleEn = step.up_next_en ?? "";
  } else if (substep === "fill") {
    focus = "fill";
    sayLabel =
      step.blank_total && step.blank_index != null
        ? `Blank ${(step.blank_index ?? 0) + 1} of ${step.blank_total}`
        : "Fill in";
    instructionEn =
      instructionEn || "Type the missing word(s). Replay the CD if you need another listen.";
  } else if (substep === "choose" || substep === "read_check") {
    focus = "choose";
    sayLabel = chooseMulti ? "Select all that apply" : "Choose one";
    instructionEn = instructionEn || "Tap your answer, then check.";
  } else if (substep === "note") {
    focus = "note";
    sayLabel = "Your notes";
    instructionEn = instructionEn || "Type brief notes about what you heard.";
  } else if (substep === "kanji_study") {
    focus = "kanji_study";
    sayLabel = "Kanji words";
    instructionEn = instructionEn || "Check each kanji and reading, then continue.";
  } else if (substep === "kanji_read") {
    focus = "passage";
    sayLabel = "Read with care";
    instructionEn = instructionEn || "Read the example lines, noticing the new kanji.";
  } else if (substep === "kanji_type") {
    focus = "kanji_type";
    const kp = step.kanji_prompt;
    sayLabel =
      kp?.total && kp.index != null ? `Type ${(kp.index ?? 0) + 1} of ${kp.total}` : "Type the kanji";
    instructionEn = instructionEn || "Type the word with your keyboard / IME.";
  } else if (substep === "read" || substep === "reflect") {
    focus = passageJp || passageEn ? "passage" : "none";
    sayLabel = substep === "reflect" ? "Life & culture" : "Read";
    instructionEn =
      instructionEn ||
      (substep === "reflect"
        ? "Read the culture note, then continue."
        : "Read the passage, then continue.");
  } else if (state === "intro_chat") {
    focus = "none";
    instructionEn = instructionEn || "Warm-up — answer freely in any language.";
  } else if (state === "grammar") {
    if (sayTargetJp) {
      focus = "say";
      sayLabel = "Say this line";
      instructionEn =
        step.instruction_en || instructionEn || "Grammar drill — say the Japanese line below.";
    } else {
      focus = "none";
      instructionEn =
        step.instruction_en || instructionEn || "Look at this pattern in your worksheet, then continue.";
    }
  } else if (expects) {
    focus = sayTargetJp || sayAlternates.length ? "say" : "none";
    if (substep === "select") {
      sayLabel = "Say the phrase";
      instructionEn = instructionEn || pictureHint || "Match the picture in your book.";
    } else if (substep === "vocab_say") {
      sayLabel = glossEn ? `Say this (${glossEn})` : "Say this word";
    } else if (substep === "pronounce") {
      sayLabel = "Pronounce clearly";
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

  const bookPage = payload.book_page ?? payload.pdf_pages?.[0] ?? null;
  const bookPageLabel =
    bookPage != null
      ? state === "grammar"
        ? `Worksheet p. ${bookPage}`
        : `Book p. ${bookPage}`
      : null;

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
    blankPromptJp,
    blankCount,
    blankIndex: step.blank_index ?? null,
    blankTotal: step.blank_total ?? null,
    choices,
    chooseMulti,
    glossEn,
    passageJp,
    passageEn,
    kanjiItems,
    kanjiPrompt,
    substeps: step.substeps ?? [],
    substepIndex: step.substep_index ?? null,
    bookPageLabel,
  };
}
