/** UI model for the tutor stage (mascot + say-this card). */

export type TutorLineColor = "yellow" | "orange" | null;

export type TutorStageModel = {
  activityLabel: string;
  stepLabel: string;
  instructionEn: string;
  hintEn: string;
  tutorBubbleJp: string;
  tutorBubbleEn: string;
  showSayCard: boolean;
  sayLabel: string;
  sayTargetJp: string | null;
  sayAlternates: string[];
  lineColor: TutorLineColor;
  listenPreview: boolean;
  pictureHint: string | null;
  showShadowCard: boolean;
};

const SUBSTEP_LABELS: Record<string, string> = {
  listen: "Listen",
  shadow: "Shadow",
  repeat: "Repeat",
  select: "Choose & say",
  partner: "Role-play · partner",
  learner: "Role-play · your line",
  swap_learner: "Role-play · you first (swapped)",
  swap_partner: "Role-play · partner (swapped)",
  pronounce: "Pronunciation",
  vocab_say: "Vocabulary",
  trace: "Trace",
  reply: "Can-do reply",
  free_answer: "Warm-up answer",
  rate: "Self-check",
};

const MODE_LABELS: Record<string, string> = {
  listen_repeat: "Listen & repeat",
  listen_repeat_all: "Listen & repeat each",
  listen_select: "Listen & choose",
  shadow_dialog: "Shadowing",
  dialog: "Dialog practice",
  pronunciation: "Pronunciation",
  vocab_drill: "Vocabulary",
  kana_trace: "Kana trace",
  intro_chat: "Warm-up",
  self_check: "Self-check",
};

function lastAssistantContent(messages: any[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m?.role === "assistant" && !m?.step?.help) return m.content || "";
  }
  return "";
}

function lastAssistantHint(messages: any[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m?.role === "assistant" && !m?.step?.help && m.hint_en) return m.hint_en;
  }
  return "";
}

export function buildTutorStageModel(session: any): TutorStageModel {
  const step = session?.step || {};
  const activity = session?.activity;
  const messages = session?.messages || [];
  const phase = step.phase || session?.state || "";
  const sub = step.book_substep || "";
  const phrases: string[] = activity?.key_phrases || [];

  let activityLabel = "Lesson";
  if (session?.state === "intro_chat" || phase === "intro_chat") {
    activityLabel = "Warm-up questions";
  } else if (session?.state === "self_check" || phase === "self_check") {
    activityLabel = "Can-do self-check";
  } else if (activity?.book_activity) {
    activityLabel = `Book activity ${activity.book_activity}`;
    if (step.section_title_en) activityLabel += ` · ${step.section_title_en}`;
  } else if (session?.state === "can_do_quiz") {
    activityLabel = "Can-do check";
  } else if (phase === "intro") {
    activityLabel = "Introduction";
  }

  const mode = step.book_mode || activity?.book_mode;
  const stepLabel =
    SUBSTEP_LABELS[sub] ||
    (mode ? MODE_LABELS[mode] || mode : phase === "quiz" ? "Can-do" : phase);

  const hintEn = session?.hint_en || lastAssistantHint(messages) || "";
  const tutorBubbleJp =
    step.partner_jp ||
    (sub === "partner" || sub === "swap_partner" ? step.dialog_line_jp : "") ||
    lastAssistantContent(messages);

  let instructionEn = step.instruction_en || hintEn || "";
  let sayTargetJp: string | null = step.say_target_jp ?? null;
  let sayAlternates: string[] = step.say_alternates_jp || step.expected_phrases || [];
  let lineColor: TutorLineColor = step.book_line_color || null;
  let showSayCard = false;
  let sayLabel = "Say this";
  let listenPreview = false;
  let pictureHint: string | null = step.picture_hint_en || activity?.picture_hint_en || null;
  let tutorBubbleEn = hintEn;
  let showShadowCard = Boolean(step.shadow_card || sub === "shadow");

  if (!sayTargetJp && phrases.length && (sub === "repeat" || sub === "select" || sub === "reply")) {
    sayTargetJp = phrases[0];
    if (!sayAlternates.length) sayAlternates = phrases.slice(1, 4);
  }
  if (!sayTargetJp && step.dialog_line_jp && step.expect_speech) {
    sayTargetJp = step.dialog_line_jp;
    lineColor = lineColor || "orange";
  }

  if (sub === "listen") {
    listenPreview = true;
    showSayCard = Boolean(sayTargetJp || pictureHint);
    sayLabel = sayTargetJp ? "After the CD, you will say" : "While you listen";
    instructionEn = instructionEn || step.up_next_en || "Listen to the book CD";
    tutorBubbleEn = step.up_next_en || instructionEn;
  } else if (sub === "shadow") {
    showSayCard = false;
    showShadowCard = true;
    instructionEn =
      instructionEn || "Shadow now — speak quietly along with the CD (not graded).";
  } else if (phase === "intro_chat" || session?.state === "intro_chat") {
    showSayCard = false;
    instructionEn = instructionEn || "Warm-up — answer freely.";
  } else if (step.expect_speech) {
    showSayCard = Boolean(sayTargetJp || sayAlternates.length);
    if (sub === "select") {
      sayLabel = "Say the greeting";
      instructionEn = instructionEn || pictureHint || "Match the picture in the book";
    } else if (sub === "learner" || sub === "swap_learner") {
      sayLabel = "Your line (orange in the book)";
      lineColor = "orange";
    } else if (sub === "reply") {
      sayLabel = "Your reply";
      tutorBubbleEn = pictureHint || instructionEn;
    } else if (sub === "free_answer") {
      showSayCard = false;
      sayLabel = "Your answer";
    } else {
      sayLabel = "Repeat aloud";
    }
  } else if (sub === "partner" || sub === "swap_partner") {
    showSayCard = false;
    lineColor = "yellow";
    instructionEn = instructionEn || "Yuki speaks the partner line (yellow in the book)";
  }

  if (phase === "intro") {
    showSayCard = false;
    showShadowCard = false;
    instructionEn = "Your tutor will guide you through the book exercises";
  }

  return {
    activityLabel,
    stepLabel,
    instructionEn,
    hintEn,
    tutorBubbleJp,
    tutorBubbleEn,
    showSayCard,
    sayLabel,
    sayTargetJp,
    sayAlternates,
    lineColor,
    listenPreview,
    pictureHint,
    showShadowCard,
  };
}
