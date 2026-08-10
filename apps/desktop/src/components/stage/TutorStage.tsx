import type { Grade, TutorPayload } from "../../api/types";
import type { AvatarMood } from "../../state/tutorPhase";
import { buildTutorStageModel } from "../../lib/tutorDisplay";
import { Avatar } from "./Avatar";
import { BookPage, shouldShowBookOnStage } from "./BookPage";
import { FocusCard } from "./FocusCard";
import { GradeResult } from "./GradeResult";
import { SpeechBubble } from "./SpeechBubble";
import { StepHeader } from "./StepHeader";

type Props = {
  payload: TutorPayload;
  mood: AvatarMood;
  level: number;
  reduceMotion: boolean;
  lastGrade: Grade | null;
  lastRecordingUrl: string | null;
  textSubmitDisabled?: boolean;
  onReplayTutor: () => void;
  onReplayBook: () => void;
  onPlayTarget: (text: string) => void;
  onTryAgain?: () => void;
  onSubmitText?: (text: string) => void;
};

/**
 * Lesson stage. When a textbook page is available, uses a split layout:
 * readable book on the left, compact tutor coach on the right.
 */
export function TutorStage({
  payload,
  mood,
  level,
  reduceMotion,
  lastGrade,
  lastRecordingUrl,
  textSubmitDisabled,
  onReplayTutor,
  onReplayBook,
  onPlayTarget,
  onTryAgain,
  onSubmitText,
}: Props) {
  const model = buildTutorStageModel(payload);
  const hasBookAudio =
    (payload.step?.play_audio?.length ?? 0) > 0 ||
    (payload.step?.retry_audio?.length ?? 0) > 0 ||
    (payload.activity?.audio?.length ?? 0) > 0;
  const bookwork = shouldShowBookOnStage(payload);
  const offerRetryHelp = Boolean(payload.step?.offer_retry_help) && lastGrade?.passed === false;

  const coach = (
    <div className="stage__coach">
      <p className="instruction">{model.instructionEn}</p>

      <div className="presence">
        <Avatar mood={mood} level={level} reduceMotion={reduceMotion} />
        <SpeechBubble
          jp={model.tutorBubbleJp}
          en={model.tutorBubbleEn}
          onReplay={onReplayTutor}
          onReplayBook={hasBookAudio ? onReplayBook : undefined}
        />
      </div>

      <FocusCard
        model={model}
        onPlayTarget={onPlayTarget}
        onSubmitText={onSubmitText}
        textSubmitDisabled={textSubmitDisabled}
      />

      <GradeResult
        grade={lastGrade}
        recordingUrl={lastRecordingUrl}
        offerRetryHelp={offerRetryHelp}
        hasBookRecording={hasBookAudio}
        onHearBook={onReplayBook}
        onTryAgain={onTryAgain}
        onHearTarget={() => {
          const target = lastGrade?.best_match || model.sayTargetJp;
          if (target) onPlayTarget(target);
        }}
      />
    </div>
  );

  if (!bookwork) {
    return (
      <div className="stage" data-layout="coach">
        <StepHeader model={model} />
        {coach}
      </div>
    );
  }

  return (
    <div className="stage" data-layout="bookwork">
      <div className="stage__head">
        <StepHeader model={model} />
      </div>
      <aside className="stage__book" aria-label="Textbook page">
        <BookPage payload={payload} variant="stage" />
      </aside>
      <section className="stage__coach-wrap" aria-label="Tutor">
        {coach}
      </section>
    </div>
  );
}
