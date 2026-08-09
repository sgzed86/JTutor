import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api } from "../api/client";
import type { DeepPartial, UserSettings } from "../api/types";
import { DEFAULT_SETTINGS, SettingsContext } from "./useSettings";

function mergeDeep(base: UserSettings, changes: DeepPartial<UserSettings>): UserSettings {
  const next: Record<string, unknown> = { ...base };
  for (const [key, section] of Object.entries(changes)) {
    if (section && typeof section === "object") {
      next[key] = { ...(base[key as keyof UserSettings] as object), ...section };
    }
  }
  return next as UserSettings;
}

/** Applies appearance settings to the document so CSS can react to them. */
function applyAppearance(settings: UserSettings) {
  const root = document.documentElement;
  const theme = settings.appearance.theme;
  const resolved =
    theme === "system"
      ? window.matchMedia("(prefers-color-scheme: light)").matches
        ? "light"
        : "dark"
      : theme;
  root.dataset.theme = resolved;
  root.dataset.textSize = settings.appearance.text_size;
  root.dataset.jpFont = settings.appearance.japanese_font;
  root.dataset.reduceMotion = settings.appearance.reduce_motion ? "true" : "false";
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    api
      .getSettings(controller.signal)
      .then((value) => {
        if (cancelled) return;
        setSettings(value);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  useEffect(() => {
    applyAppearance(settings);
    if (settings.appearance.theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: light)");
    const listener = () => applyAppearance(settings);
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, [settings]);

  const update = useCallback(async (changes: DeepPartial<UserSettings>) => {
    // Optimistic: the UI should never wait on a settings round-trip.
    setSettings((current) => mergeDeep(current, changes));
    try {
      const saved = await api.patchSettings(changes);
      setSettings(saved);
    } catch {
      /* the optimistic value stands for this session */
    }
  }, []);

  const reset = useCallback(async () => {
    try {
      setSettings(await api.resetSettings());
    } catch {
      setSettings(DEFAULT_SETTINGS);
    }
  }, []);

  const value = useMemo(() => ({ settings, loaded, update, reset }), [settings, loaded, update, reset]);
  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}
