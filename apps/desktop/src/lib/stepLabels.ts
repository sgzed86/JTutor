/**
 * The one place the UI names modes and sub-steps.
 *
 * There used to be two maps with different wording for the same keys
 * (`lib/tutorDisplay.ts` and `components/ModeCard.tsx`), plus a third copy of
 * the flow rules in `Tutor.tsx`. The flow rules now come from the server; only
 * the words live here.
 */

export type ModeInfo = { title: string; description: string; icon: string };

export const MODE_INFO: Record<string, ModeInfo> = {
  listen_repeat: { title: "Listen & repeat", description: "Play the CD, then say the same phrase.", icon: "🔁" },
  listen_repeat_all: { title: "Listen & repeat each", description: "Play the CD once, then say every item in order.", icon: "🔢" },
  listen_fill: { title: "Listen & fill in", description: "Play the CD, then type the missing words.", icon: "✏️" },
  listen_choose: { title: "Listen & choose", description: "Play the CD, then tap what you heard.", icon: "✅" },
  listen_select: { title: "Choose & say", description: "Match the picture in your book, then say the phrase.", icon: "🖼" },
  note_take: { title: "Listen & note", description: "Play the CD, then type short notes.", icon: "📝" },
  reading: { title: "Reading", description: "Read the passage, then answer.", icon: "📖" },
  vocab_drill: { title: "Vocabulary", description: "Learn the words — meaning, then say each one.", icon: "📚" },
  pronunciation: { title: "Pronunciation", description: "Listen carefully, then say each item clearly.", icon: "🗣️" },
  culture_read: { title: "Life & culture", description: "Read the culture note for this lesson.", icon: "🏯" },
  kanji_words: { title: "Kanji words", description: "Study the lesson kanji, read examples, then type them.", icon: "漢" },
  shadow_dialog: { title: "Shadowing", description: "Speak quietly along with the dialog. Not graded.", icon: "🎧" },
  dialog: { title: "Role-play", description: "Partner line, your line, then swap roles.", icon: "💬" },
  intro_chat: { title: "Warm-up", description: "Answer a short question — any language is fine.", icon: "👋" },
  self_check: { title: "Self-check", description: "Rate how well you managed this Can-do.", icon: "⭐" },
  repeat: { title: "Listen & repeat", description: "Play the CD, then say the same phrase.", icon: "🔁" },
};

export const SUBSTEP_LABEL: Record<string, string> = {
  listen: "Listen",
  shadow: "Shadow",
  repeat: "Repeat",
  fill: "Fill in",
  choose: "Choose",
  note: "Notes",
  read: "Read",
  read_check: "Check",
  select: "Choose & say",
  vocab_say: "Vocabulary",
  pronounce: "Pronunciation",
  reflect: "Life & culture",
  kanji_study: "Kanji words",
  kanji_read: "Read kanji lines",
  kanji_type: "Type kanji",
  partner: "Partner line",
  learner: "Your line",
  swap_learner: "Swap — you first",
  swap_partner: "Swap — partner",
  reply: "Can-do reply",
  free_answer: "Your answer",
  rate: "Rate yourself",
};

export const PHASE_LABEL: Record<string, string> = {
  lesson_intro: "Introduction",
  intro_chat: "Warm-up",
  book: "Book practice",
  grammar: "Grammar",
  can_do_quiz: "Can-do check",
  self_check: "Self-check",
  lesson_complete: "Complete",
};

export function modeInfo(mode: string | null | undefined): ModeInfo {
  return MODE_INFO[mode || ""] ?? MODE_INFO.listen_repeat;
}

export function substepLabel(substep: string | null | undefined): string | null {
  if (!substep) return null;
  return SUBSTEP_LABEL[substep] ?? substep;
}
