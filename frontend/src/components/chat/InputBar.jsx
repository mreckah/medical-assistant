import { Send, Paperclip } from "lucide-react";

export const InputBar = ({
  inputRef,
  fileRef,
  sendMessage,
  setSelectedImage,
  loading,
}) => {
  return (
    <div className="flex items-center gap-2 rounded-2xl
      bg-white border border-slate-200 shadow-md p-2">
      
      <input
        type="file"
        ref={fileRef}
        hidden
        accept="image/*"
        onChange={(e) => setSelectedImage(e.target.files[0])}
      />

      <button
        onClick={() => fileRef.current.click()}
        className="p-2 rounded-xl hover:bg-teal-50 transition"
      >
        <Paperclip size={18} className="text-teal-600" />
      </button>

      <input
        ref={inputRef}
        placeholder="Describe your symptoms..."
        className="flex-1 bg-transparent outline-none text-sm px-2 text-slate-700"
        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
      />

      <button
        onClick={sendMessage}
        disabled={loading}
        className="flex items-center gap-1
        bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-xl text-sm transition"
      >
        <Send size={16} />
        Send
      </button>
    </div>
  );
};
