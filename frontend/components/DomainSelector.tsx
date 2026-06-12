"use client";

interface Props {
  domains: string[];
  activeDomain: string;
  onChange: (d: string) => void;
}

export default function DomainSelector({ domains, activeDomain, onChange }: Props) {
  if (domains.length === 0) {
    return (
      <p className="text-[#475569] text-xs italic">No domains yet</p>
    );
  }

  return (
    <select
      value={activeDomain}
      onChange={(e) => onChange(e.target.value)}
      className="w-full bg-[#1e293b] text-[#e2e8f0] text-sm rounded-md px-3 py-1.5 border border-[#334155] focus:outline-none focus:ring-1 focus:ring-slate-500 cursor-pointer"
    >
      {domains.map((d) => (
        <option key={d} value={d}>
          {d}
        </option>
      ))}
    </select>
  );
}
