import { createContext, useContext, useEffect, useState } from "react";

const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:3000";

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [chats, setChats] = useState([]); 
  const [activeChatId, setActiveChatId] = useState(null); 
  const [messages, setMessages] = useState([]); 
  
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);
  const [selectedImage, setSelectedImage] = useState(null);
  const [medicalReport, setMedicalReport] = useState(null);
  
  const [message, setMessage] = useState(null);

  // --- 1. LOAD CHATS ---
  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = async () => {
    try {
      const res = await fetch(`${backendUrl}/chats`);
      const data = await res.json();
      setChats(data);
      // We do NOT auto-select here. User starts with 0 active chats.
    } catch (err) {
      console.error("Failed to fetch chats", err);
    }
  };

  // --- 2. CREATE NEW CHAT ---
  const createNewChat = async () => {
    try {
      const res = await fetch(`${backendUrl}/chats`, { method: "POST" });
      const newChat = await res.json();
      
      setChats((prev) => [...prev, newChat]);
      switchChat(newChat.id); 
      return newChat.id; // Return ID for immediate use
    } catch (err) {
      console.error("Error creating chat", err);
      return null;
    }
  };

  // --- 3. DELETE CHAT (FIXED) ---
  const deleteChat = async (id) => {
    try {
      await fetch(`${backendUrl}/chats/${id}`, { method: "DELETE" });
      setChats((prev) => prev.filter((c) => c.id !== id));
      
      if (activeChatId === id) {
        // If we deleted the active chat, RESET everything immediately
        setActiveChatId(null);
        setMessages([]);
        setMedicalReport(null);
        
        // --- FIX IS HERE ---
        // Force stop loading and audio playback
        setLoading(false);
        setMessage(null); 
        // -------------------
      }
    } catch (err) {
      console.error("Error deleting chat", err);
    }
  };

  // --- 4. SWITCH CHAT ---
  const switchChat = async (id) => {
    setActiveChatId(id);
    setLoading(true);
    setMessages([]); 
    
    // Stop any current audio when switching
    setMessage(null);

    try {
      const res = await fetch(`${backendUrl}/chats/${id}`);
      const data = await res.json();
      
      const historyMessages = (data.messages || []).map(msg => ({
        ...msg,
        played: true 
      }));

      setMessages(historyMessages);
      setMedicalReport(data.report);
    } catch (err) {
      console.error("Error fetching chat details", err);
    } finally {
      setLoading(false);
    }
  };

  // --- 5. SEND MESSAGE (AUTO-CREATE LOGIC) ---
  const chat = async (textMessage, audioBlob = null) => {
    let currentChatId = activeChatId;

    setLoading(true);

    // If no chat is active, create one FIRST
    if (!currentChatId) {
        currentChatId = await createNewChat();
        if (!currentChatId) {
            setLoading(false);
            return; // Error creating chat
        }
    }

    const formData = new FormData();
    formData.append("chatId", currentChatId); 
    if (textMessage) formData.append("message", textMessage);
    if (audioBlob) formData.append("audio", audioBlob, "recording.wav");
    if (selectedImage) formData.append("image", selectedImage);

    const userMsg = { role: "user", text: textMessage || "(Audio/Image)", played: true };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        body: formData,
      });
      const resp = await res.json();

      if (resp.messages) {
        const newAiMessages = resp.messages.map(msg => ({ ...msg, played: false }));
        setMessages((prev) => [...prev, ...newAiMessages]);
      }

      if (resp.report) setMedicalReport(resp.report);
      if (resp.imageProcessed) setSelectedImage(null);
      
      fetchChats(); 

    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  // --- AUDIO LOGIC ---
  useEffect(() => {
     if (!messages.length) return;
     const nextMsg = messages.find(m => m.role !== 'user' && !m.played && m.audio);
     if (nextMsg) setMessage(nextMsg);
     else setMessage(null);
  }, [messages]);

  const onMessagePlayed = () => {
     setMessages((prev) => prev.map(m => {
        if (m === message) return { ...m, played: true };
        return m;
     }));
  };

  return (
    <ChatContext.Provider
      value={{
        chat,
        message,
        messages, 
        chats,    
        activeChatId,
        switchChat,
        createNewChat,
        deleteChat,
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
        selectedImage,
        setSelectedImage,
        medicalReport,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error("useChat must be used within a ChatProvider");
  return context;
};
