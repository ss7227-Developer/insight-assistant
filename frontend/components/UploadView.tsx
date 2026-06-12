"use client";

import { useCallback, useRef, useState } from "react";
import { ingestFiles } from "@/lib/api";

interface Props {
  onIngested: () => void;
}

type Status = "idle" | "uploading" | "success" | "error";

const ACCEPTED = ".txt,.md,.pdf,.docx,.csv,.xlsx,.json";

export default function UploadView({ onIngested }: Props) {
  const [domain, setDomain] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = (incoming: FileList | null) => {
    if (!incoming) return;
    const arr = Array.from(incoming);
    setFiles((prev) => {
      const names = new Set(prev.map((f) => f.name));
      return [...prev, ...arr.filter((f) => !names.has(f.name))];
    });
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }, []);

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };
  const onDragLeave = () => setDragging(false);

  const removeFile = (name: string) =>
    setFiles((prev) => prev.filter((f) => f.name !== name));

  const submit = async () => {
    if (!domain.trim() || files.length === 0) return;
    setStatus("uploading");
    setMessage("");

    try {
      const res = await ingestFiles(domain.trim(), files);
      setStatus("success");
      setMessage(
        `Ingested ${res.files_ingested} file(s) into domain "${res.domain}" — ${res.chunks_indexed} chunks indexed.`
      );
      setFiles([]);
      setDomain("");
      onIngested();
    } catch (err: unknown) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Upload failed");
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="px-6 py-4 border-b border-slate-200 flex-shrink-0">
        <h1 className="font-semibold text-slate-900 text-base">Upload Documents</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Supported: .txt .md .pdf .docx .csv .xlsx .json
        </p>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-6 max-w-2xl w-full mx-auto space-y-5">
        {/* Domain name */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Domain name
          </label>
          <input
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="e.g. finance, legal, hr-policies"
            className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 placeholder:text-slate-400"
          />
          <p className="text-xs text-slate-400 mt-1">
            Use lowercase identifiers. Uploading to an existing domain appends to it.
          </p>
        </div>

        {/* Drop zone */}
        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
            dragging
              ? "border-slate-500 bg-slate-50"
              : "border-slate-300 hover:border-slate-400 hover:bg-slate-50"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept={ACCEPTED}
            className="hidden"
            onChange={(e) => addFiles(e.target.files)}
          />
          <p className="text-3xl mb-2">📂</p>
          <p className="text-sm font-medium text-slate-700">
            Drag & drop files here, or click to browse
          </p>
          <p className="text-xs text-slate-400 mt-1">Multiple files accepted</p>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <ul className="space-y-1.5">
            {files.map((f) => (
              <li
                key={f.name}
                className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm"
              >
                <span className="text-slate-700 truncate max-w-xs">{f.name}</span>
                <button
                  onClick={() => removeFile(f.name)}
                  className="text-slate-400 hover:text-red-500 ml-3 flex-shrink-0 transition-colors"
                  aria-label="Remove"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}

        {/* Status message */}
        {message && (
          <div
            className={`rounded-xl px-4 py-3 text-sm ${
              status === "success"
                ? "bg-green-50 border border-green-200 text-green-700"
                : "bg-red-50 border border-red-200 text-red-700"
            }`}
          >
            {message}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={submit}
          disabled={!domain.trim() || files.length === 0 || status === "uploading"}
          className="w-full bg-slate-900 text-white rounded-xl py-2.5 text-sm font-medium hover:bg-slate-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {status === "uploading" ? "Ingesting…" : "Ingest & Index"}
        </button>
      </div>
    </div>
  );
}
