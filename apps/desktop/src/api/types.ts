/** Shapes returned by the Jtutor backend. Mirrors backend/app/orchestrator._payload. */

export type LessonState =
  | "lesson_intro"
  | "intro_chat"
  | "book"
  | "grammar"
  | "can_do_quiz"
  | "self_check"
  | "lesson_complete";

export type SubStep =
  | "listen"
  | "shadow"
  | "repeat"
  | "fill"
  | "choose"
  | "note"
  | "read"
  | "read_check"
  | "select"
  | "partner"
  | "learner"
  | "swap_learner"
  | "swap_partner"
  | "vocab_say"
  | "pronounce"
  | "trace"
  | "reflect"
  | "kanji_study"
  | "kanji_read"
  | "kanji_type"
  | "reply"
  | "free_answer"
  | "rate";

export type BookMode =
  | "listen_repeat"
  | "listen_repeat_all"
  | "listen_fill"
  | "listen_choose"
  | "listen_select"
  | "note_take"
  | "reading"
  | "dialog"
  | "shadow_dialog"
  | "pronunciation"
  | "vocab_drill"
  | "kana_trace"
  | "culture_read"
  | "kanji_words"
  | "repeat"
  | "intro_chat"
  | "self_check";

export type AudioEntry = {
  path: string;
  transcript?: string | null;
};

export type Segment = {
  index: number;
  total: number;
  can_do_id?: string | null;
  title_en?: string | null;
};

export type Step = {
  phase?: string;
  book_mode?: BookMode;
  book_substep?: SubStep;
  activity_id?: string;
  book_activity?: number;
  kind?: string;
  section_title_en?: string | null;

  /** Self-describing flow data — the client must not re-derive these. */
  substeps?: SubStep[];
  substep_index?: number | null;
  substep_total?: number;
  substep_label_en?: string | null;
  expects_speech?: boolean;
  expects_text?: boolean;
  auto_advance?: boolean;
  graded?: boolean;
  activity_index?: number;
  activity_total?: number;
  segment?: Segment | null;

  /** Legacy aliases kept for one release. */
  expect_speech?: boolean;
  auto_advance_after_audio?: boolean;

  play_audio?: string[];
  audio?: AudioEntry[];
  dialog_script?: DialogLine[];
  dialog_line_jp?: string;
  dialog_speaker?: "partner" | "learner";
  book_line_color?: "yellow" | "orange" | null;
  partner_jp?: string;
  expected_phrases?: string[];
  say_target_jp?: string | null;
  /** Practice steps: Yuki speaks this target before the mic opens. */
  model_before_speech?: boolean;
  /**
   * After a missed spoken answer: show Hear CD / Hear Yuki / Try again
   * instead of auto-replaying the recording.
   */
  offer_retry_help?: boolean;
  /** Book CD paths available on demand when offer_retry_help is set (not auto-played). */
  retry_audio?: string[];
  say_alternates_jp?: string[];
  /** Cloze prompt with ＿ placeholders (answers stay on the server). */
  blank_prompt_jp?: string | null;
  blank_count?: number;
  blank_index?: number | null;
  blank_total?: number | null;
  choices?: { id: string; label_jp?: string | null; label_en?: string | null }[];
  choose_multi?: boolean;
  gloss_en?: string | null;
  passage_jp?: string | null;
  passage_en?: string | null;
  culture_notes_en?: string | null;
  expects_notes?: boolean;
  note_prompt_en?: string | null;
  kanji_items?: { kanji?: string | null; reading?: string | null; gloss_en?: string | null }[];
  kanji_sentences?: string[];
  kanji_prompt?: {
    kanji?: string | null;
    reading?: string | null;
    gloss_en?: string | null;
    index?: number | null;
    total?: number | null;
  } | null;
  picture_hint_en?: string | null;
  instruction_en?: string | null;
  up_next_en?: string | null;
  shadow_card?: boolean;
  phrase_index?: number | null;
  phrase_total?: number | null;
  grammar_index?: number;
  grammar_total?: number;
  grammar_point?: string;
  grammar_count?: number;
  can_do_id?: string;
  statement_en?: string;
  statement_jp?: string;
  help?: boolean;
  next_lesson_id?: string | null;
};

export type DialogLine = { speaker: "partner" | "learner"; jp: string };

export type Message = {
  role: "assistant" | "user";
  content: string;
  hint_en?: string;
  spoken?: boolean;
  kind?: "question";
  step?: Step;
  state?: string;
};

export type Rubric = { must_include?: string[]; min_score?: number };

export type CanDo = {
  id: string;
  can_do_number?: number;
  statement_en?: string;
  statement_jp?: string;
  rubric?: Rubric;
  passes?: number;
  spoken_passes?: number;
  best_score?: number;
  mastered?: boolean;
};

export type Activity = {
  id: string;
  kind?: string;
  book_activity?: number;
  book_mode?: BookMode;
  can_do_id?: string;
  key_phrases?: string[];
  prompt_en?: string;
  picture_hint_en?: string;
  picture_has_image?: boolean;
  dialog_script?: DialogLine[];
  audio?: string[];
  book_section_en?: string;
  pdf_page?: number | null;
};

export type DiffRun = { text: string; match: boolean };

export type Grade = {
  passed?: boolean;
  score?: number;
  similarity?: number;
  hits?: string[];
  gaps?: string[];
  best_match?: string | null;
  feedback_en?: string;
  feedback_jp?: string;
  jp_feedback?: string;
  spoken?: boolean;
  transcript?: string;
  diff?: DiffRun[];
};

export type ProgressSnapshot = {
  fraction: number;
  percent: number;
  phase: string;
  label: string;
};

export type SelfCheckSummary = {
  can_do_id: string;
  statement_en?: string;
  self_stars?: number | null;
  self_comment?: string | null;
};

export type GrammarPoint = {
  point: string;
  worksheet_pages?: unknown[];
  pattern_en?: string;
  prompt_en?: string;
  prompt_jp?: string;
  examples?: Array<string | { jp: string; en?: string }>;
};
export type VocabItem = { jp?: string; en?: string };

export type TutorPayload = {
  kind: "step" | "help";
  session_id: number;
  lesson_id: string;
  lesson_title_en?: string | null;
  book_id?: string | null;
  state: LessonState;
  activity_id: string | null;
  activity: Activity | null;
  messages: Message[];
  lesson_messages: Message[];
  help_messages: Message[];
  can_dos: CanDo[];
  quiz_index: number;
  step: Step | null;
  hint_en?: string | null;
  progress: ProgressSnapshot;
  segments: Segment[];
  grammar: GrammarPoint[];
  vocab: VocabItem[];
  grade: Grade | null;
  self_check: { can_do_id: string; statement_en?: string; statement_jp?: string } | null;
  self_checks: SelfCheckSummary[];
  next_lesson_id: string | null;
  /** Lesson textbook page range from the curriculum, e.g. [101, 123]. */
  pdf_pages?: number[];
  /** Best page to open right now (interpolated within the lesson range). */
  book_page?: number | null;
  lesson_meta?: {
    english_notes?: string;
    portfolio_prompts?: string[];
    pdf_pages?: number[];
  };
};

export type LessonSummary = {
  lesson_id: string;
  book_id?: string;
  title_en?: string;
  topic_en?: string;
  unlocked: boolean;
  mastered: boolean;
  can_dos: CanDo[];
};

export type ResumeHint = {
  lesson_id: string;
  title_en?: string;
  title_jp?: string;
  phase?: string;
  phase_label?: string;
  phase_hint?: string;
  percent?: number;
  has_session?: boolean;
  activity_id?: string | null;
  updated_at?: string | null;
};

export type ProgressOverview = {
  book_id?: string;
  book_title?: string;
  lessons: LessonSummary[];
  resume?: ResumeHint | null;
};

export type ServiceState = { ok: boolean; required: boolean };

export type Health = {
  ok: boolean;
  instance_id: string;
  app: string;
  ollama: { ok: boolean; models?: string[]; selected?: string; error?: string };
  voicevox: { ok: boolean; status?: number; error?: string };
  whisper: { ok: boolean; state: string; loaded: boolean; model: string; error?: string | null };
  services: Record<string, ServiceState>;
  settings: Record<string, unknown>;
};

export type VoiceSpeakerOption = {
  speaker_id: number;
  name: string;
  style_name: string;
  style_type?: string;
  label: string;
};

export type BookInfo = { id: string; title: string; level: string; available: boolean; active: boolean };

export type SrsCard = {
  id: number;
  card_type: string;
  lesson_id: string;
  front: string;
  back: string;
};

export type Transcript = {
  text: string;
  language: string;
  duration_s?: number;
  avg_logprob?: number | null;
  no_speech_prob?: number | null;
};

export type UserSettings = {
  prefs_version?: number;
  voice: {
    speaker_id: number | null;
    speed: number;
    pitch: number;
    fallback_to_system_voice: boolean;
  };
  audio: {
    input_device_id: string | null;
    output_device_id: string | null;
    tutor_volume: number;
    book_volume: number;
    book_rate: number;
    duck_tutor_under_book: boolean;
  };
  appearance: {
    theme: "system" | "light" | "dark";
    text_size: "normal" | "large";
    japanese_font: "mincho" | "gothic";
    reduce_motion: boolean;
  };
  lessons: {
    auto_advance: "off" | "after_audio" | "after_audio_and_answer";
    auto_advance_delay_ms: number;
    auto_start_recording: boolean;
    mic_mode: "hold" | "toggle";
    auto_stop_on_silence: boolean;
    silence_ms: number;
    max_recording_ms: number;
    confirm_before_send: boolean;
    grading_strictness: "lenient" | "standard" | "strict";
    show_romaji: boolean;
    show_furigana: boolean;
  };
  ask_yuki: {
    answer_language: "en" | "ja" | "both";
    speak_answer: boolean;
    answer_length: "brief" | "normal" | "detailed";
    model: string | null;
  };
  advanced: {
    whisper_model: string | null;
    whisper_device: string | null;
    developer_tools: boolean;
  };
};

export type DeepPartial<T> = { [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K] };
