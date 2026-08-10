import { useCallback, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ContextPanel } from "../components/context/ContextPanel";
import { NoticeStack } from "../components/feedback/NoticeStack";
import { SelfCheckModal } from "../components/stage/SelfCheckModal";
import { TutorStage } from "../components/stage/TutorStage";
import { TransportBar } from "../components/transport/TransportBar";
import { useSettings } from "../state/useSettings";
import { useTutorSession } from "../state/useTutorSession";

type Props = {
  onLessonChange: (lessonId: string) => void;
  onProgressChanged: () => void;
  contextOpen: boolean;
  onToggleContext: () => void;
  onContextOpenChange?: (open: boolean) => void;
};

export function TutorPage({
  onLessonChange,
  onProgressChanged,
  contextOpen,
  onToggleContext,
  onContextOpenChange,
}: Props) {
  const { lessonId = "L01" } = useParams();
  const navigate = useNavigate();
  const { settings } = useSettings();
  const session = useTutorSession(lessonId, settings);
  const { payload, phase, presentation, actions, recorder, audio } = session;

  useEffect(() => onLessonChange(lessonId), [lessonId, onLessonChange]);

  useEffect(() => {
    if (payload?.state === "lesson_complete") onProgressChanged();
  }, [onProgressChanged, payload?.state]);

  // Book lives on the main stage — keep the helper drawer closed on phase changes
  // so the page stays wide. Learners can still open Ask Yuki manually.
  useEffect(() => {
    if (!payload || !onContextOpenChange) return;
    const bookOnStage =
      Boolean(payload.book_page ?? payload.pdf_pages?.[0]) &&
      (payload.state === "book" || payload.state === "grammar" || payload.state === "lesson_intro");
    if (bookOnStage) onContextOpenChange(false);
  }, [payload?.lesson_id, payload?.state, onContextOpenChange]);

  // Space: tap to start/stop in toggle mode; press-and-hold in hold mode.
  useEffect(() => {
    const isTypingTarget = (target: EventTarget | null) =>
      target instanceof HTMLElement && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
    const hold = settings.lessons.mic_mode === "hold";

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.code !== "Space" || e.repeat || isTypingTarget(e.target)) return;
      if (hold) {
        if (phase.kind !== "awaiting_speech") return;
        e.preventDefault();
        actions.startRecording("answer");
        return;
      }
      if (phase.kind === "awaiting_speech") {
        e.preventDefault();
        actions.startRecording("answer");
      } else if (phase.kind === "recording") {
        e.preventDefault();
        actions.stopRecording();
      }
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (!hold) return;
      if (e.code !== "Space" || isTypingTarget(e.target)) return;
      if (phase.kind === "recording") {
        e.preventDefault();
        actions.stopRecording();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
    };
  }, [actions, phase.kind, settings.lessons.mic_mode]);

  const speak = useCallback((text: string) => void audio.play([{ kind: "tts", text }]), [audio]);

  const goToNextLesson = useCallback(() => {
    const next = payload?.next_lesson_id;
    if (!next) return;
    onProgressChanged();
    navigate(`/tutor/${next}`);
  }, [navigate, onProgressChanged, payload?.next_lesson_id]);

  const onPrimary = useCallback(() => {
    if (presentation.primary.id === "next_lesson") {
      goToNextLesson();
      return;
    }
    actions.runPrimaryAction();
  }, [actions, goToNextLesson, presentation.primary.id]);

  return (
    <>
      <main className="main">
        {payload ? (
          <TutorStage
            payload={payload}
            mood={presentation.mood}
            level={audio.level || recorder.level}
            reduceMotion={settings.appearance.reduce_motion}
            lastGrade={session.lastGrade}
            lastRecordingUrl={session.lastRecordingUrl}
            textSubmitDisabled={phase.kind === "grading"}
            onReplayTutor={actions.replayTutorLine}
            onReplayBook={actions.replayBookAudio}
            onPlayTarget={speak}
            onTryAgain={actions.tryAgainAfterMiss}
            onSubmitText={(text) => void actions.sendAnswer(text, false)}
          />
        ) : phase.kind === "blocked" ? (
          <div className="stage__placeholder">
            <div className="panel empty-state">
              <h2>{phase.reason === "lesson_locked" ? "This lesson is still locked" : "Can't open this lesson"}</h2>
              <p>{phase.message}</p>
              <button type="button" className="btn btn--primary" onClick={() => navigate(`/tutor/L01`)}>
                Go to the first lesson
              </button>
            </div>
          </div>
        ) : (
          <div className="stage__placeholder">
            <span className="spinner" aria-hidden /> Opening the lesson…
          </div>
        )}
      </main>

      {contextOpen && (
        <ContextPanel
          payload={payload}
          asking={session.asking}
          recordingQuestion={recorder.recording && recorder.purpose === "question"}
          onAsk={(text) => void actions.ask(text)}
          onCancelAsk={actions.cancelAsk}
          onAskByVoice={() =>
            recorder.recording ? actions.stopRecording() : actions.startRecording("question")
          }
          onSpeak={speak}
        />
      )}

      <TransportBar
        phase={phase}
        presentation={presentation}
        micMode={settings.lessons.mic_mode}
        recording={recorder.recording}
        waveform={recorder.waveform}
        pendingAdvance={session.pendingAdvance}
        developerTools={settings.advanced.developer_tools}
        canReplay={Boolean(payload)}
        canSkip={Boolean(payload) && payload?.state !== "lesson_complete"}
        onSkip={() => void actions.advance()}
        onPrimary={onPrimary}
        onPressStart={() => actions.startRecording("answer")}
        onPressEnd={actions.stopRecording}
        onReplayTutor={actions.replayTutorLine}
        onReplayBook={actions.replayBookAudio}
        onCancelPendingAdvance={actions.cancelPendingAdvance}
        onRestart={() => void actions.restart()}
        onJumpCanDo={(reset) => void actions.jumpToCanDo(reset)}
        onToggleContext={onToggleContext}
      />

      <SelfCheckModal
        open={phase.kind === "self_check"}
        statementEn={payload?.self_check?.statement_en}
        statementJp={payload?.self_check?.statement_jp}
        busy={presentation.busy}
        onSubmit={(stars, comment) => void actions.submitSelfCheck(stars, comment)}
        onSkip={() => void actions.advance()}
      />

      <NoticeStack notices={session.notices} onDismiss={session.dismissNotice} />
    </>
  );
}
