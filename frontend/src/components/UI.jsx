import { useRef, useEffect, useState } from "react";
import { useChat } from "../hooks/useChat";

export const UI = ({ hidden, ...props }) => {
  const input = useRef();
  const { 
    chat, 
    loading, 
    cameraZoomed, 
    setCameraZoomed, 
    message,
    messages,         
    chats,           
    activeChatId,
    switchChat,
    createNewChat,
    deleteChat,       
    selectedImage,     
    setSelectedImage   
  } = useChat();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null); 

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = () => {
    const text = input.current.value;
    if (!loading && !message && (text || selectedImage)) {
      chat(text);
      input.current.value = "";
    }
  };

  if (hidden) return null;

  return (
    <>
      <div className="fixed inset-0 z-10 pointer-events-none font-sans text-slate-800">
        
        {/* --- LEFT SIDEBAR TOGGLE --- */}
        <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className={`pointer-events-auto absolute top-6 p-2.5 transition-all duration-500 ease-in-out rounded-xl bg-white border border-slate-200 shadow-lg z-[60] ${
              sidebarOpen ? "left-[18.5rem] text-slate-500" : "left-6 text-emerald-600"
            }`}
        >
           {sidebarOpen ? (
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
           ) : (
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" /></svg>
           )}
        </button>

        {/* --- SIDEBAR --- */}
        <div 
          className={`absolute inset-y-0 left-0 bg-white/95 backdrop-blur-2xl border-r border-slate-200/60 pointer-events-auto flex flex-col transition-all duration-500 ease-in-out z-50 overflow-hidden ${
            sidebarOpen ? "w-80 translate-x-0 shadow-2xl" : "w-0 -translate-x-full"
          }`}
        >
          {/* Header/New Session */}
          <div className={`px-6 pt-20 pb-8 flex flex-col items-center transition-all duration-300 ${sidebarOpen ? "opacity-100" : "opacity-0"}`}>
             <button onClick={createNewChat} className="group relative flex items-center justify-center w-16 h-16 bg-emerald-600 text-white hover:bg-emerald-700 shadow-xl rounded-2xl transition-transform hover:scale-105">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor" className="w-8 h-8"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
             </button>
             <span className="mt-3 text-[10px] font-bold text-slate-400 tracking-[0.2em] uppercase whitespace-nowrap">New Session</span>
          </div>
          
          {/* Chat List with Delete Buttons */}
          <div className={`flex-1 overflow-y-auto px-4 flex flex-col gap-2 transition-opacity duration-300 ${sidebarOpen ? "opacity-100" : "opacity-0"}`}>
             <div className="min-w-[280px]">
                {chats.map((chat) => (
                    <div key={chat.id} className="relative group mb-2">
                        <button 
                            onClick={() => switchChat(chat.id)} 
                            className={`w-full text-left px-5 pr-12 py-4 rounded-2xl text-[10px] font-bold tracking-wider transition-all ${
                                activeChatId === chat.id 
                                ? "bg-emerald-50 text-emerald-800 border border-emerald-100 shadow-sm" 
                                : "text-slate-500 hover:bg-slate-50"
                            }`}
                        >
                            {chat.title.toUpperCase()}
                        </button>
                        
                        {/* --- THE REMOVE BUTTON --- */}
                        <button 
                            onClick={(e) => { 
                                e.stopPropagation(); // Prevents switching chat when deleting
                                deleteChat(chat.id); 
                            }}
                            className="absolute right-4 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-slate-300 hover:text-rose-500 hover:bg-rose-50 opacity-0 group-hover:opacity-100 transition-all"
                            title="Remove Consultation"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                ))}
             </div>
          </div>
        </div>

        {/* --- RIGHT CONVERSATION HISTORY --- */}
        <div className="absolute top-24 right-6 bottom-32 w-80 pointer-events-none flex flex-col gap-4">
           <div className="flex-1 overflow-y-auto pointer-events-auto pr-2 flex flex-col gap-4 custom-scrollbar">
              {messages.map((msg, index) => (
                <div key={index} className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}>
                  <div className={`max-w-[90%] px-4 py-3 rounded-2xl text-xs leading-relaxed shadow-sm ${
                    msg.sender === "user" 
                    ? "bg-emerald-600 text-white rounded-tr-none" 
                    : "bg-white/80 backdrop-blur-md text-slate-700 border border-white rounded-tl-none"
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
           </div>
        </div>

        {/* --- TOP RIGHT CONTROLS --- */}
        <div className="absolute top-6 right-6 pointer-events-auto z-20">
           <button
            onClick={() => setCameraZoomed(!cameraZoomed)}
            className={`w-12 h-12 flex items-center justify-center rounded-2xl transition-all shadow-lg border ${cameraZoomed ? "bg-emerald-600 border-emerald-500 text-white" : "bg-white/90 border-slate-200 text-slate-400 hover:text-emerald-600"}`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
          </button>
        </div>

        {/* --- INPUT AREA --- */}
        <div className={`absolute bottom-8 right-0 left-0 flex justify-center px-6 transition-all duration-500 z-20 ${sidebarOpen ? "pl-80" : "pl-0"}`}>
            <div className="w-full max-w-2xl flex flex-col gap-3 pointer-events-auto">
                <div className="flex items-center gap-4 bg-white/90 backdrop-blur-3xl p-3 pl-5 rounded-[2.5rem] border border-white shadow-2xl shadow-emerald-900/10">
                    <button onClick={() => fileInputRef.current.click()} className="text-slate-400 hover:text-emerald-600 transition-colors p-1">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
                    </button>
                    <input type="file" ref={fileInputRef} onChange={(e) => setSelectedImage(e.target.files[0])} accept="image/*" className="hidden" />
                    <input className="flex-1 bg-transparent border-none focus:ring-0 text-sm font-medium placeholder:text-slate-400" placeholder="Type a message to your medical assistant..." ref={input} onKeyDown={(e) => e.key === "Enter" && sendMessage()} />
                    <button disabled={loading || message} onClick={sendMessage} className={`h-12 px-8 rounded-[1.8rem] text-xs font-black tracking-widest uppercase transition-all ${loading || message ? "bg-slate-100 text-slate-300 cursor-not-allowed" : "bg-emerald-600 text-white hover:bg-emerald-700 shadow-lg shadow-emerald-200"}`}>
                        {loading ? "..." : "Ask"}
                    </button>
                </div>
            </div>
        </div>
      </div>
    </>
  );
};