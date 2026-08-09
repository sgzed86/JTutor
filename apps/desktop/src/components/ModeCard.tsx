const MODE_LABELS: Record<string, { title: string; desc: string; icon: string }> = {
  listen_repeat: {
    title: "Listen & repeat",
    desc: "Play the CD, then say the same phrase.",
    icon: "🔁",
  },
  listen_repeat_all: {
    title: "Listen & repeat each",
    desc: "Play the CD once, then say every item in order.",
    icon: "🔢",
  },
  listen_select: {
    title: "Choose & say",
    desc: "Match the book picture, then say the phrase.",
    icon: "🖼",
  },
  shadow_dialog: {
    title: "Shadowing",
    desc: "Speak quietly along with the full dialog CD. No grading.",
    icon: "🎧",
  },
  dialog: {
    title: "Role-play",
    desc: "Partner line, your line, then swap roles.",
    icon: "💬",
  },
  intro_chat: {
    title: "Warm-up",
    desc: "Answer a short personal question — any language is OK.",
    icon: "👋",
  },
  self_check: {
    title: "Self-check",
    desc: "Rate how well you can do this Can-do (stars).",
    icon: "⭐",
  },
};

const SUB_LABELS: Record<string, string> = {
  listen: "Listening",
  shadow: "Shadow now",
  repeat: "Your turn — repeat",
  select: "Picture choice",
  partner: "Partner line",
  learner: "Your line",
  swap_learner: "Swap — you first",
  swap_partner: "Swap — partner",
  reply: "Can-do reply",
  free_answer: "Your answer",
  rate: "Rate yourself",
};

type Props = {
  bookMode?: string | null;
  bookSubstep?: string | null;
  pictureHasImage?: boolean;
};

export function ModeCard({ bookMode, bookSubstep, pictureHasImage }: Props) {
  const key =
    bookSubstep === "shadow"
      ? "shadow_dialog"
      : bookMode && MODE_LABELS[bookMode]
        ? bookMode
        : "listen_repeat";
  const mode = MODE_LABELS[key] || MODE_LABELS.listen_repeat;
  const sub = bookSubstep ? SUB_LABELS[bookSubstep] || bookSubstep : null;

  return (
    <div className={`mode-card mode-${key}`} role="status">
      <span className="mode-card-icon" aria-hidden>
        {mode.icon}
      </span>
      <div className="mode-card-body">
        <span className="mode-card-title">{mode.title}</span>
        {sub && <span className="mode-card-step">{sub}</span>}
        <p className="mode-card-desc muted">
          {mode.desc}
          {pictureHasImage && bookMode === "listen_select" ? " Use the illustration in your book." : ""}
        </p>
      </div>
    </div>
  );
}
