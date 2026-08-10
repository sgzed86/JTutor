/**
 * Yuki — illustrated tutor.
 *
 * Face stays on a stable idle still. Mouth frames are masked overlays so the
 * head never jumps. Visemes follow speech onsets (syllable attacks) from the
 * audio envelope instead of raw volume thresholds, which tracks TTS better.
 */

import { useEffect, useRef, useState } from "react";
import type { AvatarMood } from "../../state/tutorPhase";

import blinkSrc from "../../assets/yuki/blink.jpg";
import idleSrc from "../../assets/yuki/idle.jpg";
import listeningSrc from "../../assets/yuki/listening.jpg";
import speakASrc from "../../assets/yuki/speak-a.jpg";
import speakOSrc from "../../assets/yuki/speak-o.jpg";
import thinkingSrc from "../../assets/yuki/thinking.jpg";

type Props = {
  mood: AvatarMood;
  /** 0..1 output level from the audio pipeline; drives the visemes. */
  level?: number;
  reduceMotion?: boolean;
};

type Mouth = "closed" | "oh" | "ah";

const MOOD_CAPTION: Record<AvatarMood, string> = {
  idle: "Here with you",
  speaking: "Speaking",
  listening: "Listening",
  thinking: "Thinking",
  celebrating: "Nice work!",
  encouraging: "Keep going",
};

const MOOD_SRC: Record<Exclude<AvatarMood, "speaking">, string> = {
  idle: idleSrc,
  listening: listeningSrc,
  thinking: thinkingSrc,
  celebrating: speakASrc,
  encouraging: listeningSrc,
};

const ALL_SRCS = [idleSrc, blinkSrc, speakOSrc, speakASrc, listeningSrc, thinkingSrc];

/**
 * Syllable-style lip sync: open on energy attacks, hold through the vowel,
 * close in the gaps. Alternates oh/ah on successive peaks so it doesn't look
 * like a single flap.
 */
function useSyllableMouth(level: number, speaking: boolean, reduceMotion: boolean): Mouth {
  const [mouth, setMouth] = useState<Mouth>("closed");
  const levelRef = useRef(level);
  const speakingRef = useRef(speaking);
  const envRef = useRef(0);
  const prevEnvRef = useRef(0);
  const mouthRef = useRef<Mouth>("closed");
  const openUntilRef = useRef(0);
  const coolUntilRef = useRef(0);
  const flipRef = useRef(false);

  levelRef.current = level;
  speakingRef.current = speaking;

  useEffect(() => {
    let raf = 0;
    let cancelled = false;

    const set = (next: Mouth) => {
      if (mouthRef.current === next) return;
      mouthRef.current = next;
      setMouth(next);
    };

    const tick = (t: number) => {
      if (cancelled) return;

      if (!speakingRef.current) {
        envRef.current *= 0.8;
        prevEnvRef.current = envRef.current;
        set("closed");
        raf = requestAnimationFrame(tick);
        return;
      }

      if (reduceMotion) {
        set(levelRef.current > 0.05 ? "oh" : "closed");
        raf = requestAnimationFrame(tick);
        return;
      }

      // Fast envelope follow — attack quick, release medium.
      const raw = Math.min(1, levelRef.current * 1.15);
      const prev = envRef.current;
      const rising = raw > prev;
      envRef.current = prev + (raw - prev) * (rising ? 0.55 : 0.22);
      const env = envRef.current;
      const delta = env - prevEnvRef.current;
      prevEnvRef.current = env;

      // Syllable onset: sharp rise above a gate.
      const onset = delta > 0.045 && env > 0.08 && t >= coolUntilRef.current;
      if (onset) {
        flipRef.current = !flipRef.current;
        // Louder peaks → wider "ah"; lighter → "oh".
        const next: Mouth = env > 0.28 ? "ah" : flipRef.current ? "oh" : "ah";
        set(next);
        // Hold through typical mora length (~80–160ms).
        openUntilRef.current = t + 90 + env * 100;
        coolUntilRef.current = t + 70; // avoid double-triggers
      } else if (t < openUntilRef.current) {
        // Keep current open shape during the vowel.
        if (mouthRef.current === "closed") set(env > 0.22 ? "ah" : "oh");
      } else if (env < 0.06) {
        set("closed");
      } else if (env < 0.14 && mouthRef.current === "ah") {
        // Ease wide open down to a smaller shape before closing.
        set("oh");
        openUntilRef.current = t + 50;
      }

      raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
    };
  }, [reduceMotion]);

  return mouth;
}

export function Avatar({ mood, level = 0, reduceMotion = false }: Props) {
  const [blinking, setBlinking] = useState(false);
  const [displayMood, setDisplayMood] = useState<AvatarMood>(mood);
  const [prevSrc, setPrevSrc] = useState<string | null>(null);
  const mouth = useSyllableMouth(level, mood === "speaking", reduceMotion);

  useEffect(() => {
    for (const url of ALL_SRCS) {
      const img = new Image();
      img.src = url;
    }
  }, []);

  useEffect(() => {
    if (reduceMotion || mood === "celebrating") {
      setBlinking(false);
      return;
    }
    let cancelled = false;
    let openTimer: ReturnType<typeof setTimeout> | undefined;
    let closeTimer: ReturnType<typeof setTimeout> | undefined;
    const schedule = () => {
      const gap =
        mood === "speaking" ? 2800 + Math.random() * 3200 : 4200 + Math.random() * 3800;
      closeTimer = setTimeout(() => {
        if (cancelled) return;
        setBlinking(true);
        openTimer = setTimeout(() => {
          if (cancelled) return;
          setBlinking(false);
          schedule();
        }, 120);
      }, gap);
    };
    schedule();
    return () => {
      cancelled = true;
      if (openTimer) clearTimeout(openTimer);
      if (closeTimer) clearTimeout(closeTimer);
    };
  }, [mood, reduceMotion]);

  useEffect(() => {
    if (mood === displayMood) return;
    const from =
      displayMood === "speaking"
        ? idleSrc
        : MOOD_SRC[displayMood as Exclude<AvatarMood, "speaking">];
    if (!reduceMotion) setPrevSrc(from);
    setDisplayMood(mood);
    if (reduceMotion) {
      setPrevSrc(null);
      return;
    }
    const t = window.setTimeout(() => setPrevSrc(null), 280);
    return () => window.clearTimeout(t);
  }, [mood, displayMood, reduceMotion]);

  const speaking = displayMood === "speaking";
  const baseSrc = speaking
    ? idleSrc
    : blinking && (displayMood === "idle" || displayMood === "encouraging")
      ? blinkSrc
      : MOOD_SRC[displayMood as Exclude<AvatarMood, "speaking">];

  const showOh = speaking && mouth === "oh";
  const showAh = speaking && mouth === "ah";
  const showBlink = speaking && blinking && mouth === "closed";

  return (
    <div className="avatar" data-mood={mood} data-alive={speaking && !reduceMotion ? "1" : "0"} data-style="illust">
      <div className="avatar__caption">
        <span className="avatar__name">Yuki</span>
        <span>{MOOD_CAPTION[mood]}</span>
      </div>
      <div className="avatar__frame">
        {prevSrc && (
          <img
            className="avatar__photo avatar__photo--fade-out"
            src={prevSrc}
            alt=""
            aria-hidden
            draggable={false}
          />
        )}
        <img
          className="avatar__photo"
          src={baseSrc}
          alt={`Yuki, ${MOOD_CAPTION[mood]}`}
          draggable={false}
        />
        {/* Mouth-only overlays keep eyes/hair locked while speaking. */}
        <img
          className="avatar__photo avatar__photo--mouth"
          src={speakOSrc}
          alt=""
          aria-hidden
          draggable={false}
          style={{ opacity: showOh ? 1 : 0 }}
        />
        <img
          className="avatar__photo avatar__photo--mouth"
          src={speakASrc}
          alt=""
          aria-hidden
          draggable={false}
          style={{ opacity: showAh ? 1 : 0 }}
        />
        <img
          className="avatar__photo avatar__photo--blink"
          src={blinkSrc}
          alt=""
          aria-hidden
          draggable={false}
          style={{ opacity: showBlink ? 1 : 0 }}
        />
        <span className="avatar__ring" aria-hidden />
      </div>
    </div>
  );
}
