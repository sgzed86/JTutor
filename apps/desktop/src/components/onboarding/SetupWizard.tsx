import { useEffect, useState } from "react";
import type { Health } from "../../api/types";
import { Dialog } from "../ui/Dialog";

/**
 * Replaces the developer checklist on the old /setup page. Each dependency
 * explains what it is for and what degrades without it, and can be skipped.
 */
export function SetupWizard({
  open,
  health,
  onClose,
  onRefresh,
}: {
  open: boolean;
  health: Health | null;
  onClose: () => void;
  onRefresh: () => void;
}) {
  const [micOk, setMicOk] = useState<boolean | null>(null);

  useEffect(() => {
    if (!open) return;
    navigator.mediaDevices
      ?.enumerateDevices()
      .then((devices) => setMicOk(devices.some((d) => d.kind === "audioinput")))
      .catch(() => setMicOk(false));
  }, [open]);

  const steps = [
    {
      key: "voicevox",
      ok: Boolean(health?.voicevox?.ok),
      title: "VOICEVOX — Yuki's voice",
      description: "Without it the lesson runs, but Yuki's lines are text only.",
      action: { label: "Download", url: "https://voicevox.hiroshiba.jp/" },
    },
    {
      key: "ollama",
      ok: Boolean(health?.ollama?.ok),
      title: "Ollama — Ask Yuki answers",
      description: "Without it, Ask Yuki falls back to showing the phrase you need.",
      action: { label: "Download", url: "https://ollama.com/" },
    },
    {
      key: "materials",
      ok: true,
      title: "Your Irodori materials",
      description:
        "Put the official PDFs and MP3s in your assets folder. Lessons work without them, but the book audio won't play.",
      action: null,
    },
    {
      key: "mic",
      ok: micOk !== false,
      title: "Microphone",
      description: "Needed to grade what you say. Pick a device and test it in Settings → Audio.",
      action: null,
    },
  ];

  const remaining = steps.filter((s) => !s.ok).length;

  return (
    <Dialog
      open={open}
      title="Set up Jtutor"
      onClose={onClose}
      narrow={false}
      footer={
        <>
          <button type="button" className="btn btn--ghost" onClick={onRefresh}>
            Check again
          </button>
          <button type="button" className="btn btn--primary" onClick={onClose}>
            {remaining === 0 ? "All set" : "Continue anyway"}
          </button>
        </>
      }
    >
      <p className="muted">
        Jtutor runs entirely on this computer. These pieces are optional — the lesson flow works without
        any of them, you just lose the feature each one provides.
      </p>
      {steps.map((step) => (
        <div className="wizard-step" key={step.key}>
          <span className="wizard-step__dot" data-ok={step.ok} aria-hidden />
          <div>
            <p className="wizard-step__title">{step.title}</p>
            <p className="wizard-step__desc">{step.description}</p>
          </div>
          {step.action && !step.ok ? (
            <a className="btn btn--ghost" href={step.action.url} target="_blank" rel="noreferrer">
              {step.action.label}
            </a>
          ) : (
            <span className="pill">{step.ok ? "Ready" : "Optional"}</span>
          )}
        </div>
      ))}
    </Dialog>
  );
}
