/**
 * Yuki — soft Ghibli-inspired tutor avatar (PNG frame swap for blink + speaking).
 */

import { useEffect, useState } from "react";
import blinkImg from "../assets/yuki/blink.png";
import neutralImg from "../assets/yuki/neutral.png";
import speakingImg from "../assets/yuki/speaking.png";

export type MascotMood = "idle" | "speaking" | "listening";

type Props = {
  mood: MascotMood;
  className?: string;
};

const MOOD_CAPTION: Record<MascotMood, string> = {
  idle: "Here with you",
  speaking: "Speaking…",
  listening: "Listening to you…",
};

type Frame = "neutral" | "speaking" | "blink";

const FRAME_SRC: Record<Frame, string> = {
  neutral: neutralImg,
  speaking: speakingImg,
  blink: blinkImg,
};

function randomBlinkDelayMs() {
  // Idle blink every ~4–7 seconds
  return 4000 + Math.random() * 3000;
}

export function TutorMascot({ mood, className }: Props) {
  const [frame, setFrame] = useState<Frame>("neutral");
  const [mouthOpen, setMouthOpen] = useState(false);

  // Idle / listening: occasional blink
  useEffect(() => {
    if (mood === "speaking") return;

    let cancelled = false;
    let blinkTimer: ReturnType<typeof setTimeout> | undefined;
    let recoverTimer: ReturnType<typeof setTimeout> | undefined;

    const scheduleBlink = () => {
      blinkTimer = setTimeout(() => {
        if (cancelled) return;
        setFrame("blink");
        recoverTimer = setTimeout(() => {
          if (cancelled) return;
          setFrame("neutral");
          scheduleBlink();
        }, 160);
      }, randomBlinkDelayMs());
    };

    setFrame("neutral");
    scheduleBlink();

    return () => {
      cancelled = true;
      if (blinkTimer) clearTimeout(blinkTimer);
      if (recoverTimer) clearTimeout(recoverTimer);
    };
  }, [mood]);

  // Speaking: toggle mouth open/closed
  useEffect(() => {
    if (mood !== "speaking") {
      setMouthOpen(false);
      return;
    }

    setFrame("speaking");
    setMouthOpen(true);
    const id = setInterval(() => {
      setMouthOpen((open) => {
        const next = !open;
        setFrame(next ? "speaking" : "neutral");
        return next;
      });
    }, 180);

    return () => clearInterval(id);
  }, [mood]);

  const src = FRAME_SRC[frame];

  return (
    <div className={`tutor-presence ${mood}${className ? ` ${className}` : ""}`}>
      <div className="tutor-presence-meta">
        <span className="tutor-live-dot" aria-hidden />
        <span className="tutor-presence-name">Yuki</span>
        <span className="tutor-presence-caption">{MOOD_CAPTION[mood]}</span>
      </div>

      <div className="tutor-portrait-panel">
        <img
          src={src}
          alt=""
          className={`tutor-avatar-img${mouthOpen ? " mouth-open" : ""}`}
          draggable={false}
        />
      </div>
    </div>
  );
}
