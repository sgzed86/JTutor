import { memo } from "react";

type BubbleProps = {
  role: string;
  kind?: string;
  content: string;
  hintEn?: string;
};

export const ChatBubble = memo(function ChatBubble({
  role,
  kind,
  content,
  hintEn,
}: BubbleProps) {
  return (
    <div>
      <div className={`bubble ${role}${kind === "question" ? " question" : ""}`}>{content}</div>
      {hintEn && role === "assistant" && (
        <p className="muted" style={{ fontSize: "0.82rem", margin: "0.2rem 0 0.6rem 0.4rem" }}>
          {hintEn}
        </p>
      )}
    </div>
  );
});
