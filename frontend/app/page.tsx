"use client";

import { useEffect, useState } from "react";
import { fetchDomains, setSessionId } from "@/lib/api";
import DomainSelector from "@/components/DomainSelector";
import ChatView from "@/components/ChatView";
import UploadView from "@/components/UploadView";

type Tab = "chat" | "upload";

export default function Home() {
  // Fresh UUID every page load — never persisted, so uploads vanish on refresh.
  const [sessionId] = useState<string>(() => crypto.randomUUID());

  const [tab, setTab] = useState<Tab>("chat");
  const [domains, setDomains] = useState<string[]>([]);
  const [activeDomain, setActiveDomain] = useState<string>("");
  const [backendReady, setBackendReady] = useState(false);

  // Register the session ID with the API module, then fetch domains.
  useEffect(() => {
    setSessionId(sessionId);
    const init = async () => {
      try {
        const domainList = await fetchDomains();
        setDomains(domainList);
        if (domainList.includes("demo")) setActiveDomain("demo");
        else if (domainList.length > 0) setActiveDomain(domainList[0]);
        setBackendReady(true);
      } catch {
        setBackendReady(true);
      }
    };
    init();
  }, [sessionId]);

  const handleDomainsRefresh = async () => {
    try {
      const domainList = await fetchDomains();
      setDomains(domainList);
      if (!activeDomain && domainList.length > 0) setActiveDomain(domainList[0]);
    } catch {
      // ignore
    }
  };

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-[#0f172a] flex flex-col">
        <div className="px-5 py-5 border-b border-[#1e293b]">
          <span className="text-white font-semibold text-sm tracking-wide">
            Insights Assistant
          </span>
          <p className="text-[#475569] text-xs mt-0.5">RAG · FAISS · Groq</p>
        </div>

        <div className="px-4 py-4 border-b border-[#1e293b]">
          <p className="text-[#475569] text-xs uppercase tracking-wider mb-2">Domain</p>
          <DomainSelector
            domains={domains}
            activeDomain={activeDomain}
            onChange={setActiveDomain}
          />
        </div>

        <nav className="flex-1 px-3 py-3 space-y-1">
          <button
            onClick={() => setTab("chat")}
            className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
              tab === "chat"
                ? "bg-[#1e293b] text-white"
                : "text-[#94a3b8] hover:bg-[#1e293b] hover:text-white"
            }`}
          >
            💬 Chat
          </button>
          <button
            onClick={() => setTab("upload")}
            className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
              tab === "upload"
                ? "bg-[#1e293b] text-white"
                : "text-[#94a3b8] hover:bg-[#1e293b] hover:text-white"
            }`}
          >
            📂 Upload
          </button>
        </nav>

        <div className="px-5 py-4 border-t border-[#1e293b] flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              backendReady ? "bg-green-400" : "bg-yellow-400 animate-pulse"
            }`}
          />
          <span className="text-[#475569] text-xs">
            {backendReady ? "Backend ready" : "Connecting…"}
          </span>
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        {tab === "chat" ? (
          <ChatView activeDomain={activeDomain} />
        ) : (
          <UploadView onIngested={handleDomainsRefresh} />
        )}
      </main>
    </div>
  );
}
