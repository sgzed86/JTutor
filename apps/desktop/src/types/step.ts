/** Tutor step shape (mirrors backend TutorStep — Tier 3.3). */

export type TutorStep = {
  phase?: string;
  book_mode?: string;
  book_substep?: string;
  expect_speech?: boolean;
  auto_advance_after_audio?: boolean;
  play_audio?: string[];
  instruction_en?: string;
  say_target_jp?: string | null;
  help?: boolean;
  culture_notes_en?: string;
};

export type LessonMeta = {
  english_notes?: string;
  portfolio_prompts?: string[];
};

export type TutorSessionPayload = {
  phase?: string;
  phase_index?: number;
  quiz_index?: number;
  lesson_meta?: LessonMeta;
  step?: TutorStep;
};
