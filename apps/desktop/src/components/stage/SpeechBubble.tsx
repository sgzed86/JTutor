type Props = {
  jp: string;
  en?: string;
  onReplay: () => void;
  onReplayBook?: () => void;
};

export function SpeechBubble({ jp, en, onReplay, onReplayBook }: Props) {
  return (
    <div className="bubble">
      <span className="bubble__label">Yuki</span>
      <p className="bubble__jp jp">{jp}</p>
      {en && <p className="bubble__en">{en}</p>}
      <div className="bubble__actions">
        <button type="button" className="btn btn--ghost btn--icon" onClick={onReplay}>
          <span aria-hidden>↺</span> Hear again
        </button>
        {onReplayBook && (
          <button type="button" className="btn btn--ghost btn--icon" onClick={onReplayBook}>
            <span aria-hidden>💿</span> Replay CD
          </button>
        )}
      </div>
    </div>
  );
}
