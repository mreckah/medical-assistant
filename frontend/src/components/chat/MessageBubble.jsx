export const MessageBubble = ({ role, content }) => {
  const isUser = role === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}
    >
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow
          ${
            isUser
              ? "bg-teal-600 text-white rounded-br-sm"
              : "bg-white text-slate-700 border border-slate-200 rounded-bl-sm"
          }`}
      >
        {content}
      </div>
    </div>
  );
};
