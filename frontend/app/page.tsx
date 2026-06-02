"use client";

import React, { useState } from "react";

interface VideoMetadata {
  platform: string;
  video_id: string;
  creator: string;
  views: number;
  likes: number;
  comments: number;
  engagement_rate: number;
}

interface Message {
  sender: "user" | "ai";
  text: string;
}

// Dynamically reads the live backend API from the environment, falling back to localhost
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Dashboard() {
  // Input fields
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [instagramUrl, setInstagramUrl] = useState("");
  
  // App States
  const [loading, setLoading] = useState(false);
  const [ingestedData, setIngestedData] = useState<{ youtube: { metadata: VideoMetadata }; instagram: { metadata: VideoMetadata } } | null>(null);
  
  // Chat States
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // 1. Core Ingestion Trigger
  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!youtubeUrl || !instagramUrl) return alert("Please fill in both URLs.");
    
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ youtube_url: youtubeUrl, instagram_url: instagramUrl }),
      });
      const result = await res.json();
      if (res.ok) {
        setIngestedData(result.data);
      } else {
        alert(result.detail || "Ingestion Failed");
      }
    } catch (err) {
      console.error(err);
      alert("Error connecting to backend");
    } finally {
      setLoading(false);
    }
  };

  // 2. Real-time Token Streaming Consumer
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || chatLoading) return;

    const userText = inputMessage;
    setInputMessage("");
    setMessages((prev) => [...prev, { sender: "user", text: userText }]);
    setChatLoading(true);

    // Placeholder for streaming AI response
    setMessages((prev) => [...prev, { sender: "ai", text: "" }]);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          question: userText,
          metadata: ingestedData // <-- Passes the card views, likes, and metrics directly!
        }),
      });

      if (!response.body) throw new Error("No response body streamable");
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        accumulatedText += decoder.decode(value, { stream: true });
        
        // Update the last message (the AI's message) in real-time
        setMessages((prev) => {
          const updated = [...prev];
          if (updated.length > 0) {
            updated[updated.length - 1] = { sender: "ai", text: accumulatedText };
          }
          return updated;
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 font-sans">
      <header className="max-w-6xl mx-auto mb-8 border-b border-slate-800 pb-4">
        <h1 className="text-3xl font-extrabold tracking-tight bg-linear-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
          Creator Intelligence Dashboard
        </h1>
        <p className="text-slate-400 text-sm mt-1">Cross-platform content comparison pipeline using local embeddings & Groq RAG</p>
      </header>

      <main className="max-w-6xl mx-auto space-y-8">
        {/* URL Inputs Panel */}
        <section className="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-xl">
          <form onSubmit={handleIngest} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">YouTube Video URL</label>
                <input 
                  type="text" 
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="https://youtube.com/watch?v=..." 
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Instagram Reel URL</label>
                <input 
                  type="text" 
                  value={instagramUrl}
                  onChange={(e) => setInstagramUrl(e.target.value)}
                  placeholder="https://www.instagram.com/reel/..." 
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            </div>
            <button 
              type="submit" 
              disabled={loading}
              className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm px-6 py-2.5 rounded-lg disabled:opacity-50 transition-opacity"
            >
              {loading ? "Processing Pipelines..." : "Ingest & Extract Content"}
            </button>
          </form>
        </section>

        {/* Side-by-Side Analytics Grid */}
        {ingestedData && (
          <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* YouTube Panel */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-md">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-red-400">YouTube Insights</h3>
                <span className="text-xs bg-slate-950 px-2 py-1 rounded border border-slate-800 font-mono text-slate-400">ID: {ingestedData.youtube.metadata.video_id}</span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between border-b border-slate-700 py-1.5">
                  <span className="text-slate-400">Creator Channel</span>
                  <span className="font-semibold">{ingestedData.youtube.metadata.creator}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700 py-1.5">
                  <span className="text-slate-400">Total Views</span>
                  <span className="font-semibold">{ingestedData.youtube.metadata.views.toLocaleString()}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700 py-1.5">
                  <span className="text-slate-400">Likes</span>
                  <span className="font-semibold">{ingestedData.youtube.metadata.likes.toLocaleString()}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700 py-1.5">
                  <span className="text-slate-400">Comments</span>
                  <span className="font-semibold">{ingestedData.youtube.metadata.comments.toLocaleString()}</span>
                </div>
                <div className="flex justify-between pt-2">
                  <span className="text-slate-400 font-medium">Engagement Rate</span>
                  <span className="text-emerald-400 font-bold">{ingestedData.youtube.metadata.engagement_rate}%</span>
                </div>
              </div>
            </div>

            {/* Instagram Panel */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-md">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-pink-400">Instagram Insights</h3>
                <span className="text-xs bg-slate-950 px-2 py-1 rounded border border-slate-800 font-mono text-slate-400">ID: {ingestedData.instagram.metadata.video_id}</span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between border-b border-slate-700 py-1.5">
                  <span className="text-slate-400">Creator Account</span>
                  <span className="font-semibold">{ingestedData.instagram.metadata.creator}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700 py-1.5">
                  <span className="text-slate-400">Total Plays/Views</span>
                  <span className="font-semibold">
  {ingestedData.instagram.metadata.views > 0 
    ? ingestedData.instagram.metadata.views.toLocaleString() 
    : <span className="text-amber-500 text-xs font-normal border border-amber-900/50 bg-amber-900/20 px-2 py-0.5 rounded">Hidden by IG</span>}
</span>
                </div>
                <div className="flex justify-between border-b border-slate-700 py-1.5">
                  <span className="text-slate-400">Likes</span>
                  <span className="font-semibold">{ingestedData.instagram.metadata.likes.toLocaleString()}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700 py-1.5">
                  <span className="text-slate-400">Comments</span>
                  <span className="font-semibold">{ingestedData.instagram.metadata.comments.toLocaleString()}</span>
                </div>
                <div className="flex justify-between pt-2">
                  <span className="text-slate-400 font-medium">Engagement Rate</span>
                  <span className="text-emerald-400 font-bold">{ingestedData.instagram.metadata.engagement_rate}%</span>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Streaming Chat Component */}
        <section className="bg-slate-800 border border-slate-700 rounded-xl flex flex-col h-112.5 shadow-xl overflow-hidden">
          <div className="bg-slate-950 px-4 py-3 border-b border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-400">
            RAG Deep-Dive Context Comparison Chat
          </div>

          {/* Messages Wrapper */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-sm">
                <p>No query submitted yet.</p>
                <p className="text-xs text-slate-600 mt-1">Ingest data above and ask questions like "Which content hooked users better?"</p>
              </div>
            )}
            {messages.map((msg, index) => (
              <div key={index} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-xl rounded-lg p-3 text-sm ${msg.sender === "user" ? "bg-indigo-600 text-white" : "bg-slate-900 border border-slate-700 text-slate-200"}`}>
                  <p className="whitespace-pre-wrap">{msg.text || "▍"}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Form Input */}
          <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-700 bg-slate-950 flex gap-2">
            <input 
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={ingestedData ? "Ask a comparative question..." : "Please complete video ingestion first..."}
              disabled={!ingestedData || chatLoading}
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-40"
            />
            <button 
              type="submit"
              disabled={!ingestedData || chatLoading}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-lg font-medium disabled:opacity-40 transition-opacity"
            >
              Ask
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}