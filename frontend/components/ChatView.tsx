"use client";

import { useEffect, useRef, useState } from "react";
import { queryDomain, type Citation } from "@/lib/api";
import MessageBubble from "./MessageBubble";

type UserMsg = { role: "user"; content: string };
type AssistantMsg = {
  role: "assistant";
  answer: string;
  key_insights: string[];
  confidence: "high" | "medium" | "low";
  citations: Citation[];
};
type Message = UserMsg | AssistantMsg;

interface Props {
  activeDomain: string;
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}

export default function ChatView({ activeDomain }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Reset chat when domain changes
  useEffect(() => {
    setMessages([]);
    setError(null);
  }, [activeDomain]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    const q = input.trim();
    if (!q || loading || !activeDomain) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setLoading(true);

    try {
      const res = await queryDomain(q, activeDomain);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          answer: res.answer,
          key_insights: res.key_insights,
          confidence: res.confidence,
          citations: res.citations,
        },
      ]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const noDomain = !activeDomain;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-200 flex-shrink-0">
        <div>
          <h1 className="font-semibold text-slate-900 text-base">Chat</h1>
          {activeDomain ? (
            <p className="text-xs text-slate-500 mt-0.5">
              Domain: <span className="font-medium text-slate-700">{activeDomain}</span>
            </p>
          ) : (
            <p className="text-xs text-slate-400 mt-0.5">Select a domain in the sidebar</p>
          )}
        </div>
        {messages.length > 0 && (
          <button
            onClick={() => setMessages([])}
            className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
          >
            Clear
          </button>
        )}
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scrollbar-thin">
        {messages.length === 0 && !loading && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-xs">
              <p className="text-3xl mb-3">🔍</p>
              <p className="text-slate-700 font-medium">Ask anything about your documents</p>
              <p className="text-slate-400 text-sm mt-1">
                {noDomain
                  ? "Upload documents first, then select a domain."
                  : `Querying the "${activeDomain}" domain.`}
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} {...msg} />
        ))}

        {loading && <TypingIndicator />}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-6 py-4 border-t border-slate-200 bg-white">
        <div className="flex items-end gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            disabled={noDomain || loading}
            placeholder={
              noDomain
                ? "Select a domain first…"
                : "Ask a question… (Enter to send)"
            }
            className="flex-1 resize-none rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 placeholder:text-slate-400 disabled:bg-slate-50 disabled:cursor-not-allowed min-h-[42px] max-h-40 overflow-y-auto"
            style={{ height: "42px" }}
            onInput={(e) => {
              const el = e.currentTarget;
              el.style.height = "42px";
              el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
            }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || noDomain || loading}
            className="flex-shrink-0 bg-slate-900 text-white rounded-xl px-4 py-2.5 text-sm font-medium hover:bg-slate-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
