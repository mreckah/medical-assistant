import { MessageBubble } from "./MessageBubble";

export const MessagesList = ({ messages }) => {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      {messages.map((m, i) => (
        <MessageBubble key={i} role={m.role} content={m.content} />
      ))}
    </div>
  );
};
