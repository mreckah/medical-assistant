import { Plus, Trash2 } from "lucide-react";

export const Sidebar = ({
  chats,
  activeChatId,
  switchChat,
  createNewChat,
  deleteChat,
  open,
}) => {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 transition-all duration-300
      ${open ? "w-72" : "w-0 overflow-hidden"}
      bg-teal-50 border-r border-teal-100`}
    >
      <div className="p-4 pt-16">
        <button
          onClick={createNewChat}
          className="flex items-center gap-2 w-full justify-center
          bg-teal-600 text-white py-3 rounded-xl text-sm font-medium hover:bg-teal-700 transition"
        >
          <Plus size={18} /> New consultation
        </button>
      </div>

      <div className="px-2 space-y-1">
        {chats.map((c) => (
          <div key={c.id} className="group relative">
            <button
              onClick={() => switchChat(c.id)}
              className={`w-full px-4 py-2 rounded-xl text-left text-sm transition
              ${
                activeChatId === c.id
                  ? "bg-teal-600 text-white"
                  : "hover:bg-teal-100 text-slate-700"
              }`}
            >
              {c.title}
            </button>

            <button
              onClick={() => deleteChat(c.id)}
              className="absolute right-3 top-1/2 -translate-y-1/2
              opacity-0 group-hover:opacity-100 text-red-500 transition"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
};
