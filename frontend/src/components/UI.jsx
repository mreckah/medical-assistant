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
  const [chatOpen, setChatOpen] = useState(true); 
  const [recording, setRecording] = useState(false);
  
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null); 

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // --- HELPER: Remove Image ---
  const removeImage = () => {
    setSelectedImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // --- AUDIO LOGIC ---
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunks.current.push(event.data);
      };

      mediaRecorder.current.onstop = () => {
        const audioBlob = new Blob(audioChunks.current, { type: "audio/wav" });
        const audioFile = new File([audioBlob], "voice_message.wav", { type: "audio/wav" });
        if (!loading) chat(null, audioFile); 
      };

      mediaRecorder.current.start();
      setRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Could not access microphone.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && recording) {
      mediaRecorder.current.stop();
      setRecording(false);
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const toggleRecording = () => {
    if (recording) stopRecording();
    else startRecording();
  };

  // --- SEND MESSAGE ---
  const sendMessage = () => {
    const text = input.current.value;
    if (!loading && !message && (text || selectedImage)) {
      chat(text); 
      input.current.value = "";
      
      // Immediately remove the image from top preview
      removeImage(); 
    }
  };

  const handleGenerateReport = async () => {
    if (!activeChatId) return;
    try {
        const response = await fetch("http://localhost:3000/report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ chatId: activeChatId }),
        });
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `Medical_Report_${activeChatId}.pdf`; 
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    } catch(e) { console.error(e); }
  };

  if (hidden) return null;

  return (
    <>
      <div className="fixed inset-0 z-10 pointer-events-none font-sans text-slate-800">
        
        {/* --- LEFT SIDEBAR --- */}
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className={`pointer-events-auto absolute top-6 p-2.5 rounded-xl bg-white border border-slate-200 shadow-lg z-[60] transition-all ${sidebarOpen ? "left-[18.5rem] text-slate-500" : "left-6 text-emerald-600"}`}>
           <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d={sidebarOpen ? "M15.75 19.5L8.25 12l7.5-7.5" : "M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"} /></svg>
        </button>
        
        {/* FIXED CONTAINER: Added overflow-hidden to prevent 'broken' look */}
        <div className={`absolute inset-y-0 left-0 bg-white/95 backdrop-blur-2xl border-r border-slate-200/60 pointer-events-auto flex flex-col transition-all duration-500 z-50 ${sidebarOpen ? "w-80 translate-x-0" : "w-0 -translate-x-full overflow-hidden"}`}>
            
            {/* WRAPPER: Controls Opacity and Fixed Width (w-80) so text doesn't squash */}
            <div className={`flex flex-col h-full w-80 transition-opacity duration-300 ${sidebarOpen ? "opacity-100" : "opacity-0 invisible"}`}>
                <div className="pt-20 px-6 flex flex-col items-center">
                    <button onClick={createNewChat} className="w-16 h-16 bg-emerald-600 text-white rounded-2xl flex items-center justify-center hover:scale-105 transition-transform shadow-xl"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor" className="w-8 h-8"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg></button>
                </div>
                <div className="flex-1 overflow-y-auto px-4 mt-8 flex flex-col gap-2">
                    {chats.map(chat => (
                        <div key={chat.id} className="group relative">
                            <button onClick={() => switchChat(chat.id)} className={`w-full text-left px-5 py-4 rounded-2xl text-[10px] font-bold tracking-wider ${activeChatId === chat.id ? "bg-emerald-50 text-emerald-800 border-emerald-100" : "text-slate-500 hover:bg-slate-50"}`}>{chat.title?.toUpperCase() || "NEW SESSION"}</button>
                            <button onClick={(e) => {e.stopPropagation(); deleteChat(chat.id)}} className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 text-slate-300 hover:text-rose-500"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>
                        </div>
                    ))}
                </div>
            </div>
        </div>

        {/* --- MESSAGES AREA --- */}
        <div className={`absolute top-24 right-6 bottom-32 w-[26rem] flex flex-col gap-4 transition-all duration-500 ${chatOpen ? "translate-x-0 opacity-100" : "translate-x-10 opacity-0"}`}>
           <div className="flex-1 overflow-y-auto pointer-events-auto pr-4 pl-4 flex flex-col gap-6 custom-scrollbar pb-10">
             {messages.map((msg, index) => (
                 <div key={index} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                   
                   {/* WRAPPER: Flex Column to stack Text then Image */}
                   <div className={`flex flex-col gap-2 max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                     
                     {/* TEXT BUBBLE */}
                     <div className={`px-5 py-4 rounded-3xl text-sm shadow-sm ${msg.role === "user" ? "bg-emerald-600 text-white rounded-br-none" : "bg-white/95 text-slate-800 border border-white rounded-bl-none"}`}>
                       {msg.text}
                     </div>

                     {/* IMAGE: Now renders beneath the bubble */}
                     {msg.image && (
                       <div className="rounded-xl overflow-hidden shadow-sm border-2 border-white max-w-[200px]">
                         <img 
                           src={msg.image instanceof File ? URL.createObjectURL(msg.image) : msg.image} 
                           alt="uploaded" 
                           className="w-full h-auto object-cover"
                         />
                       </div>
                     )}

                   </div>
                 </div>
             ))}
             <div ref={messagesEndRef} />
           </div>
        </div>

        {/* --- TOP RIGHT CONTROLS --- */}
        <div className="absolute top-6 right-6 pointer-events-auto z-20 flex gap-3">
            {messages.length > 0 && <button onClick={handleGenerateReport} className="h-12 px-4 rounded-2xl bg-white/90 border border-slate-200 text-slate-600 hover:text-emerald-600 shadow-lg text-xs font-bold uppercase">Report</button>}
            <button onClick={() => setChatOpen(!chatOpen)} className={`w-12 h-12 flex items-center justify-center rounded-2xl shadow-lg border ${chatOpen ? "bg-emerald-600 border-emerald-500 text-white" : "bg-white/90 text-slate-400"}`}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" /></svg>
            </button>
            <button onClick={() => setCameraZoomed(!cameraZoomed)} className={`w-12 h-12 flex items-center justify-center rounded-2xl shadow-lg border ${cameraZoomed ? "bg-emerald-600 border-emerald-500 text-white" : "bg-white/90 text-slate-400"}`}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
            </button>
        </div>

        {/* --- INPUT AREA --- */}
        <div className={`absolute bottom-8 right-0 left-0 flex justify-center px-6 transition-all duration-500 z-20 ${sidebarOpen ? "pl-80" : "pl-0"}`}>
            <div className="w-full max-w-2xl flex flex-col gap-3 pointer-events-auto relative">
                
                {/* --- IMAGE PREVIEW (BEFORE SENDING) --- */}
                {selectedImage && (
                    <div className="absolute bottom-full mb-4 left-4 z-30 animate-in fade-in zoom-in duration-300">
                        <div className="relative group">
                            <div className="w-20 h-20 rounded-xl overflow-hidden border-2 border-white shadow-xl bg-slate-100">
                                <img 
                                    src={URL.createObjectURL(selectedImage)} 
                                    alt="Selected" 
                                    className="w-full h-full object-cover" 
                                />
                            </div>
                            <button 
                                onClick={removeImage}
                                className="absolute -top-2 -right-2 w-6 h-6 bg-rose-500 hover:bg-rose-600 text-white rounded-full flex items-center justify-center shadow-md transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
                                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                                </svg>
                            </button>
                        </div>
                    </div>
                )}

                <div className="flex items-center gap-4 bg-white/90 backdrop-blur-3xl p-3 pl-5 rounded-[2.5rem] border border-white shadow-2xl shadow-emerald-900/10">
                    <button onClick={() => fileInputRef.current.click()} className="text-slate-400 hover:text-emerald-600 transition-colors p-1">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
                    </button>
                    <input type="file" ref={fileInputRef} onChange={(e) => { if(e.target.files[0]) setSelectedImage(e.target.files[0]) }} accept="image/*" className="hidden" />
                    
                    <input className="flex-1 bg-transparent border-none focus:ring-0 text-sm font-medium placeholder:text-slate-400" placeholder={recording ? "Listening..." : "Type a message..."} ref={input} onKeyDown={(e) => e.key === "Enter" && sendMessage()} disabled={recording} />
                    
                    <button onClick={toggleRecording} disabled={loading || message} className={`p-3 rounded-full transition-all ${recording ? "bg-rose-500 text-white animate-pulse" : "text-slate-400 hover:text-emerald-600"}`}>
                        {recording ? <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6"><path fillRule="evenodd" d="M4.5 7.5a3 3 0 013-3h9a3 3 0 013 3v9a3 3 0 01-3 3h-9a3 3 0 01-3-3v-9z" clipRule="evenodd" /></svg>
                        : <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" /></svg>}
                    </button>

                    <button disabled={loading || message || recording} onClick={sendMessage} className={`h-12 px-8 rounded-[1.8rem] text-xs font-black tracking-widest uppercase transition-all ${loading || message ? "bg-slate-100 text-slate-300" : "bg-emerald-600 text-white hover:bg-emerald-700 shadow-lg"}`}>
                        {loading ? "..." : "Ask"}
                    </button>
                </div>
            </div>
        </div>
      </div>
    </>
  );
};