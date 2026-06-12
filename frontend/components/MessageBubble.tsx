"use client";

import { useState } from "react";
import type { Citation } from "@/lib/api";

interface AssistantMessage {
  role: "assistant";
  answer: string;
  key_insights: string[];
  confidence: "high" | "medium" | "low";
  citations: Citation[];
}

interface UserMessage {
  role: "user";
  content: string;
}

type Props = AssistantMessage | UserMessage;

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-green-100 text-green-700 border border-green-200",
  medium: "bg-yellow-100 text-yellow-700 border border-yellow-200",
  low: "bg-red-100 text-red-700 border border-red-200",
};

function Disclosure({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 transition-colors"
      >
        <span
          className={`transition-transform ${open ? "rotate-90" : ""}`}
          aria-hidden
        >
          ▶
        </span>
        {label}
      </button>
      {open && <div className="mt-2 pl-4">{children}</div>}
    </div>
  );
}

export default function MessageBubble(props: Props) {
  if (props.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[70%] bg-slate-900 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed">
          {props.content}
        </div>
      </div>
    );
  }

  const { answer, key_insights, confidence, citations } = props;

  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed">
        {/* Answer */}
        <p className="text-slate-800 whitespace-pre-wrap">{answer}</p>

        {/* Confidence badge */}
        <span
          className={`inline-block mt-2 text-xs font-medium px-2 py-0.5 rounded-full ${CONFIDENCE_STYLES[confidence] ?? CONFIDENCE_STYLES.low}`}
        >
          {confidence} confidence
        </span>

        {/* Key insights */}
        {key_insights.length > 0 && (
          <Disclosure label={`${key_insights.length} key insight${key_insights.length > 1 ? "s" : ""}`}>
            <ul className="space-y-1">
              {key_insights.map((insight, i) => (
                <li key={i} className="flex gap-2 text-slate-700 text-xs">
                  <span className="text-slate-400 mt-0.5 flex-shrink-0">•</span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          </Disclosure>
        )}

        {/* Citations */}
        {citations.length > 0 && (
          <Disclosure label={`${citations.length} citation${citations.length > 1 ? "s" : ""}`}>
            <div className="space-y-2">
              {citations.map((c, i) => (
                <div key={i} className="bg-white border border-slate-200 rounded-lg p-2">
                  <p className="text-xs font-medium text-slate-700">
                    {c.source}
                    {c.page_num != null && (
                      <span className="text-slate-400"> · p.{c.page_num}</span>
                    )}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-2 italic">
                    "{c.excerpt}"
                  </p>
                </div>
              ))}
            </div>
          </Disclosure>
        )}
      </div>
    </div>
  );
}
