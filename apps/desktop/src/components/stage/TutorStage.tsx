import type { Grade, TutorPayload } from "../../api/types";
import type { AvatarMood } from "../../state/tutorPhase";
import { buildTutorStageModel } from "../../lib/tutorDisplay";
import { Avatar } from "./Avatar";
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
  onReplayTutor: () => void;
  onReplayBook: () => void;
  onPlayTarget: (text: string) => void;
};

export function TutorStage({
  payload,
  mood,
  level,
  reduceMotion,
  lastGrade,
  lastRecordingUrl,
  onReplayTutor,
  onReplayBook,
  onPlayTarget,
}: Props) {
  const model = buildTutorStageModel(payload);
  const hasBookAudio = (payload.step?.play_audio?.length ?? 0) > 0;

  return (
    <div className="stage">
      <StepHeader model={model} />

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

      <FocusCard model={model} onPlayTarget={onPlayTarget} />

      <GradeResult
        grade={lastGrade}
        recordingUrl={lastRecordingUrl}
        onHearTarget={() => {
          const target = lastGrade?.best_match || model.sayTargetJp;
          if (target) onPlayTarget(target);
        }}
      />
    </div>
  );
}
