import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { TutorStage } from "../components/TutorStage";
import { LessonProgressBar } from "../components/LessonProgressBar";
import { SelfCheckModal } from "../components/SelfCheckModal";
import type { MascotMood } from "../components/TutorMascot";
import { buildTutorStageModel } from "../lib/tutorDisplay";
import { jlog } from "../jlog";
import { speakTutor } from "../speech";

type Step = {
  phase?: string;
  play_audio?: string[];
  expect_speech?: boolean;
  auto_advance_after_audio?: boolean;
  book_substep?: string;
  hint_en?: string;
};

export default function Tutor() {
  const { lessonId: paramId } = useParams();
  const navigate = useNavigate();
  const [lessonId, setLessonId] = useState(paramId || "L01");
  const [lessons, setLessons] = useState<any[]>([]);
  const [session, setSession] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [status, setStatus] = useState("Starting…");
  const [error, setError] = useState("");
  const [askText, setAskText] = useState("");
  const [asking, setAsking] = useState(false);
  const [lastGrade, setLastGrade] = useState<any>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const spokenLenRef = useRef(0);
  const speakingRef = useRef(false);
  const handlingRef = useRef(false);
  const recordingModeRef = useRef<"practice" | "question" | null>(null);

  useEffect(() => {
    api.progress().then((p) => setLessons(p.lessons || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (paramId) setLessonId(paramId);
  }, [paramId]);

  const playBookTracks = async (paths: string[]) => {
    for (const rel of paths) {
      const audio = new Audio(api.audioUrl(rel));
      await new Promise<void>((resolve, reject) => {
        audio.onended = () => resolve();
        audio.onerror = () => reject(new Error("Book audio failed"));
        audio.play().catch(reject);
      });
    }
  };

  const startListening = useCallback(async () => {
    if (speakingRef.current || mediaRef.current) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        mediaRef.current = null;
        setRecording(false);
        if (recordingModeRef.current !== "practice") {
          recordingModeRef.current = null;
          return;
        }
        recordingModeRef.current = null;
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size < 800) {
          setStatus("Didn't catch that — tap mic and try again");
          return;
        }
        setBusy(true);
        setStatus("Hearing you…");
        try {
          const { text: transcript } = await api.transcribe(blob);
          if (!transcript?.trim()) {
            setStatus("Couldn't hear you — tap mic to retry");
            setBusy(false);
            return;
          }
          const s = await api.message(lessonId, transcript.trim(), true);
          jlog("mic_message", { lessonId, transcript: transcript.trim().slice(0, 200) });
          if (s.grade) setLastGrade(s.grade);
          setSession(s);
        } catch (e: any) {
          setError("Mic/Whisper: " + (e.message || e));
        } finally {
          setBusy(false);
        }
      };
      mediaRef.current = rec;
      recordingModeRef.current = "practice";
      rec.start();
      setRecording(true);
      setStatus("Your turn — speak, then tap when done");
    } catch (e: any) {
      setError("Microphone: " + (e.message || e));
    }
  }, [lessonId]);

  const stopListening = useCallback(() => {
    if (mediaRef.current && mediaRef.current.state !== "inactive") {
      mediaRef.current.stop();
    }
  }, []);

  const runPipeline = useCallback(
    async (data: any, opts?: { speak?: boolean }) => {
      const shouldSpeak = opts?.speak !== false;
      if (handlingRef.current) return;
      handlingRef.current = true;
      try {
        const messages = data.messages || [];
        const assistants = messages.filter((m: any) => m.role === "assistant");
        if (assistants.length <= spokenLenRef.current) {
          handlingRef.current = false;
          return;
        }

        const newest = assistants.slice(spokenLenRef.current);
        spokenLenRef.current = assistants.length;
        const last = newest[newest.length - 1];
        const step: Step = data.step || last?.step || {};
        jlog("pipeline_step", {
          lessonId,
          quizIndex: data.quiz_index,
          phase: step.phase,
          kind: (step as any).kind,
          book_substep: step.book_substep,
          expect_speech: step.expect_speech,
          auto_advance: step.auto_advance_after_audio,
          audio_count: (step.play_audio || []).length,
          new_messages: newest.length,
          state: data.state,
          activity_id: data.activity_id,
        });

        if (shouldSpeak) {
          speakingRef.current = true;
          setSpeaking(true);
          setStatus("Tutor speaking…");
          for (const m of newest) {
            await speakTutor(m.content, api.speak);
          }
          speakingRef.current = false;
          setSpeaking(false);
        }

        const audio = step.play_audio || [];
        if (audio.length) {
          setStatus("Book audio…");
          await playBookTracks(audio);
        }

        // Only the lesson intro auto-advances once; further steps use Skip or speech grading.
        if (step.auto_advance_after_audio && step.phase === "intro") {
          setStatus("Next exercise…");
          jlog("pipeline_auto_advance", { lessonId, from: "intro" });
          const next = await api.advance(lessonId);
          setSession(next);
          return;
        }

        const autoBook = step.auto_advance_after_audio && step.phase === "book";
        const sub = step.book_substep || "";
        if (
          autoBook &&
          (sub === "listen" ||
            sub === "shadow" ||
            sub === "partner" ||
            sub === "swap_partner" ||
            sub === "announce")
        ) {
          setStatus(
            sub === "shadow" ? "Shadowing done…" : sub === "listen" ? "Your turn next…" : "Next line…"
          );
          jlog("pipeline_auto_advance", { lessonId, from: sub });
          const next = await api.advance(lessonId);
          setSession(next);
          return;
        }

        if (step.expect_speech) {
          setStatus("Your turn — speak, then tap when done");
          await startListening();
        } else {
          setStatus("Tap Skip / next step to skip this exercise");
        }
      } catch (e: any) {
        jlog("pipeline_error", { lessonId, error: String(e.message || e) });
        setError(String(e.message || e));
      } finally {
        speakingRef.current = false;
        setSpeaking(false);
        handlingRef.current = false;
      }
    },
    [lessonId, startListening]
  );

  useEffect(() => {
    if (!session?.step?.expect_speech) {
      stopListening();
    }
  }, [session?.step?.expect_speech, stopListening]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setBusy(true);
      setError("");
      spokenLenRef.current = 0;
      try {
        const s = await api.startTutor(lessonId);
        if (cancelled) return;
        if (s.locked) setError(s.error || "Lesson locked");
        const assistants = (s.messages || []).filter((m: any) => m.role === "assistant");
        spokenLenRef.current = assistants.length > 1 ? assistants.length - 1 : 0;
        setSession(s);
      } catch (e: any) {
        if (!cancelled) setError(e.message || String(e));
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [lessonId]);

  useEffect(() => {
    if (!session?.messages?.length || busy || handlingRef.current) return;
    const ac = session.messages.filter((m: any) => m.role === "assistant").length;
    if (ac <= spokenLenRef.current) return;
    void runPipeline(session);
  }, [session?.messages, busy, runPipeline]);

  async function manualAdvance() {
    stopListening();
    setBusy(true);
    try {
      const s = await api.advance(lessonId);
      jlog("manual_advance", { lessonId });
      setSession(s);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  async function jumpToCanDoQuiz(resetCanDo = false) {
    stopListening();
    setBusy(true);
    spokenLenRef.current = 0;
    setError("");
    try {
      const s = await api.jumpToCanDoQuiz(lessonId, resetCanDo);
      if (s.error) {
        setError(s.error);
        return;
      }
      jlog("jump_can_do_quiz", { lessonId, resetCanDo });
      setSession(s);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  async function submitQuestion(text: string, spoken = false) {
    const q = text.trim();
    if (!q) return;
    recordingModeRef.current = null;
    stopListening();
    setAsking(true);
    setBusy(true);
    setError("");
    try {
      const s = await api.askTutor(lessonId, q, spoken);
      jlog("ask_tutor", { lessonId, question: q.slice(0, 200) });
      setAskText("");
      setSession(s);
    } catch (e: any) {
      setError("Ask tutor: " + (e.message || e));
    } finally {
      setAsking(false);
      setBusy(false);
    }
  }

  async function askByVoice() {
    recordingModeRef.current = null;
    stopListening();
    if (speakingRef.current) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        mediaRef.current = null;
        setRecording(false);
        if (recordingModeRef.current !== "question") {
          recordingModeRef.current = null;
          return;
        }
        recordingModeRef.current = null;
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size < 800) {
          setStatus("Didn't catch that — try again");
          return;
        }
        setStatus("Hearing your question…");
        try {
          const { text: transcript } = await api.transcribe(blob);
          if (transcript?.trim()) await submitQuestion(transcript.trim(), true);
        } catch (e: any) {
          setError("Mic/Whisper: " + (e.message || e));
        }
      };
      mediaRef.current = rec;
      recordingModeRef.current = "question";
      rec.start();
      setRecording(true);
      setStatus("Ask your question, then tap when done");
    } catch (e: any) {
      setError("Microphone: " + (e.message || e));
    }
  }

  async function resetConversation() {
    stopListening();
    setBusy(true);
    spokenLenRef.current = 0;
    try {
      const s = await api.resetTutor(lessonId);
      jlog("reset_lesson", { lessonId });
      setSession(s);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  const nextLessonId =
    session?.next_lesson_id || session?.step?.next_lesson_id || null;
  const lessonComplete = session?.state === "lesson_complete";
  const selfCheck = session?.self_check;
  const showSelfCheck = session?.state === "self_check" && !!selfCheck?.can_do_id;

  async function submitSelfCheck(stars: number, comment: string) {
    if (!selfCheck?.can_do_id) return;
    setBusy(true);
    setError("");
    try {
      const s = await api.selfCheck(lessonId, selfCheck.can_do_id, stars, comment);
      jlog("self_check", { lessonId, canDoId: selfCheck.can_do_id, stars });
      setSession(s);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  function goToNextLesson() {
    if (!nextLessonId) return;
    api.progress().then((p) => setLessons(p.lessons || [])).catch(() => {});
    setLessonId(nextLessonId);
    navigate(`/tutor/${nextLessonId}`);
  }
  const activity = session?.activity;
  const messages = session?.messages || [];
  const expectSpeech = session?.step?.expect_speech;
  const stageModel = useMemo(
    () => (session ? buildTutorStageModel(session) : null),
    [session]
  );
  const mascotMood: MascotMood = speaking
    ? "speaking"
    : recording || expectSpeech
      ? "listening"
      : "idle";

  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <h1>Tutor</h1>
          <p className="muted">Yuki walks through your Irodori book with you.</p>
        </div>
        <select
          value={lessonId}
          onChange={(e) => {
            setLessonId(e.target.value);
            navigate(`/tutor/${e.target.value}`);
          }}
          style={{
            background: "var(--bg2)",
            color: "var(--ink)",
            border: "1px solid var(--line)",
            borderRadius: 10,
            padding: "0.45rem 0.7rem",
          }}
        >
          {lessons.map((l) => (
            <option
              key={l.lesson_id}
              value={l.lesson_id}
              disabled={!l.unlocked}
            >
              {l.lesson_id} {l.title_en}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="panel" style={{ borderColor: "var(--danger)" }}>{error}</div>}

      <LessonProgressBar progress={session?.progress} />

      <SelfCheckModal
        open={showSelfCheck}
        canDoId={selfCheck?.can_do_id || ""}
        statementEn={selfCheck?.statement_en}
        statementJp={selfCheck?.statement_jp}
        busy={busy}
        onSubmit={(stars, comment) => void submitSelfCheck(stars, comment)}
        onSkip={() => void manualAdvance()}
      />

      {stageModel && (
        <TutorStage
          model={stageModel}
          mood={mascotMood}
          status={status}
          expectSpeech={!!expectSpeech && !showSelfCheck}
          recording={recording}
          speaking={speaking}
          busy={busy}
          onMicClick={() => (recording ? stopListening() : startListening())}
          lastGrade={lastGrade}
          activity={activity}
          step={session?.step}
        />
      )}

      <div className="panel stack tutor-controls-compact" style={{ padding: "1rem 1.2rem" }}>
        <div className="row" style={{ flexWrap: "wrap", gap: "0.5rem", justifyContent: "center" }}>
          {lessonComplete && nextLessonId && (
            <button className="btn primary" disabled={busy || speaking} onClick={goToNextLesson}>
              Start {nextLessonId}
            </button>
          )}
          <button className="btn" disabled={busy || speaking} onClick={manualAdvance}>
            Skip / next step
          </button>
          <button className="btn" disabled={busy || speaking} onClick={() => jumpToCanDoQuiz(false)}>
            Jump to Can-do quiz
          </button>
          <button
            className="btn"
            disabled={busy || speaking}
            onClick={() => jumpToCanDoQuiz(true)}
            title="Also clears Can-do pass counts for this lesson"
          >
            Can-do (reset progress)
          </button>
          <button className="btn" disabled={busy || speaking} onClick={resetConversation}>
            Restart lesson
          </button>
        </div>

        <div className="panel stack tutor-ask-panel" style={{ marginTop: 0 }}>
          <h3 style={{ margin: 0, fontSize: "1rem" }}>Ask Yuki</h3>
          <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
            Stuck? Ask in English or Japanese — you stay on the same exercise.
          </p>
          <textarea
            value={askText}
            onChange={(e) => setAskText(e.target.value)}
            placeholder="What should I say here? What does おはよう mean?"
            rows={2}
            disabled={busy || speaking || lessonComplete}
            style={{
              width: "100%",
              resize: "vertical",
              background: "var(--bg2)",
              color: "var(--ink)",
              border: "1px solid var(--line)",
              borderRadius: 8,
              padding: "0.5rem 0.65rem",
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void submitQuestion(askText);
              }
            }}
          />
          <div className="row" style={{ gap: "0.5rem", flexWrap: "wrap" }}>
            <button
              className="btn primary"
              disabled={busy || speaking || asking || !askText.trim() || lessonComplete}
              onClick={() => submitQuestion(askText)}
            >
              {asking ? "Thinking…" : "Send question"}
            </button>
            <button
              className="btn"
              disabled={busy || speaking || lessonComplete}
              onClick={() => (recording ? stopListening() : askByVoice())}
            >
              {recording ? "Done" : "Ask by voice"}
            </button>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel stack">
          <h2>Transcript</h2>
          <div className="chat">
            {messages.map((m: any, i: number) => (
              <div key={i}>
                <div className={`bubble ${m.role}${m.kind === "question" ? " question" : ""}`}>{m.content}</div>
                {m.hint_en && m.role === "assistant" && (
                  <p className="muted" style={{ fontSize: "0.82rem", margin: "0.2rem 0 0.6rem 0.4rem" }}>
                    {m.hint_en}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
        <div className="stack">
          <div className="panel">
            <h2>Current step</h2>
            {stageModel?.showSayCard && stageModel.sayTargetJp && (
              <p style={{ fontFamily: "var(--font-display)", fontSize: "1.2rem", margin: "0 0 0.5rem" }}>
                {stageModel.sayTargetJp}
              </p>
            )}
            {activity ? (
              <>
                <p>
                  Activity {activity.book_activity} · {activity.kind}
                  {activity.book_mode ? ` · ${activity.book_mode}` : ""}
                </p>
                <p className="muted">{stageModel?.instructionEn || activity.prompt_en}</p>
              </>
            ) : (
              <p className="muted">{session?.state === "can_do_quiz" ? "Can-do role-play" : session?.state}</p>
            )}
          </div>
          <div className="panel">
            <h2>Can-dos (end of lesson)</h2>
            <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
              {(session?.can_dos || []).map((c: any) => (
                <li key={c.id}>{c.statement_en}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
