import { createContext, useContext } from "react";
import type { DeepPartial, UserSettings } from "../api/types";

export const DEFAULT_SETTINGS: UserSettings = {
  voice: { speaker_id: null, speed: 1, pitch: 0, fallback_to_system_voice: true },
  audio: {
    input_device_id: null,
    output_device_id: null,
    tutor_volume: 1,
    book_volume: 1,
    book_rate: 1,
    duck_tutor_under_book: true,
  },
  appearance: { theme: "system", text_size: "normal", japanese_font: "mincho", reduce_motion: false },
  lessons: {
    auto_advance: "after_audio",
    auto_advance_delay_ms: 1200,
    auto_start_recording: true,
    mic_mode: "hold",
    auto_stop_on_silence: true,
    silence_ms: 1200,
    max_recording_ms: 15000,
    confirm_before_send: false,
    grading_strictness: "standard",
    show_romaji: false,
    show_furigana: false,
  },
  ask_yuki: { answer_language: "both", speak_answer: true, answer_length: "normal", model: null },
  advanced: { whisper_model: null, whisper_device: null, developer_tools: false },
};

export type SettingsContextValue = {
  settings: UserSettings;
  loaded: boolean;
  update: (changes: DeepPartial<UserSettings>) => Promise<void>;
  reset: () => Promise<void>;
};

export const SettingsContext = createContext<SettingsContextValue>({
  settings: DEFAULT_SETTINGS,
  loaded: false,
  update: async () => undefined,
  reset: async () => undefined,
});

export function useSettings(): SettingsContextValue {
  return useContext(SettingsContext);
}
