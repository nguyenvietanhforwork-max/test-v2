"use client";

import Link from "next/link";
import { INDUSTRIES } from "@/lib/constants";

export function FilterChips({ current }: { current: { industry?: string; region?: string; bucket?: string } }) {
  return (
    <div className="mb-4 flex flex-wrap gap-1.5">
      <Chip href="/" active={!current.industry && !current.region && !current.bucket} label="All" />
      {INDUSTRIES.slice(0, 6).map((i) => (
        <Chip key={i.slug} href={`/?industry=${i.slug}`} active={current.industry === i.slug} label={i.name} dot={i.color} />
      ))}
      <Chip href={`/?region=VN&bucket=macro`} label="VN Macro" active={current.region === "VN" && current.bucket === "macro"} />
      <Chip href={`/?region=INT&bucket=macro`} label="Global Macro" active={current.region === "INT" && current.bucket === "macro"} />
      <Chip href={`/?bucket=corp`} label="Corporate" active={current.bucket === "corp"} />
    </div>
  );
}

function Chip({ href, label, active, dot }: { href: string; label: string; active?: boolean; dot?: string }) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition
        ${active ? "border-accent-line bg-accent-soft text-accent" : "border-line-2 bg-bg-1 text-fg-1 hover:border-line-3 hover:bg-bg-2"}`}
    >
      <span className={`size-1.5 rounded-full ${active ? "bg-accent shadow-[0_0_6px_var(--accent)]" : ""}`}
            style={dot && !active ? { background: dot } : {}} />
      {label}
    </Link>
  );
}
