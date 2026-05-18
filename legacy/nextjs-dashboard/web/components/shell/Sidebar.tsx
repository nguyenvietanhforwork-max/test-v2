"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGrid, FileText, GitBranch, Search } from "lucide-react";
import { INDUSTRIES } from "@/lib/constants";

const NAV = [
  { href: "/", icon: LayoutGrid, label: "Daily Intelligence", count: 23 },
  { href: "/reports", icon: FileText, label: "Report Center", count: 147 },
  { href: "/graph", icon: GitBranch, label: "Knowledge Graph" },
  { href: "/search", icon: Search, label: "Semantic Search" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden flex-col gap-1 overflow-y-auto border-r border-line-1 px-3 py-6 lg:flex">
      <SectionLabel>Workspace</SectionLabel>
      {NAV.map((n) => (
        <NavItem key={n.href} {...n} active={pathname === n.href} />
      ))}

      <div className="mt-5">
        <SectionLabel>Industries</SectionLabel>
        {INDUSTRIES.slice(0, 6).map((i) => (
          <NavItem key={i.slug} href={`/industries/${i.slug}`} label={i.name} count={i.todayCount}
                   dot={i.color} active={pathname === `/industries/${i.slug}`} />
        ))}
        <Link href="/industries" className="px-3 py-2 text-[12px] text-fg-2 hover:text-fg-1">Show all 28 →</Link>
      </div>

      <div className="mt-5">
        <SectionLabel>Macro</SectionLabel>
        <NavItem href="/macro/vn" label="Vietnam Macro" count={6} />
        <NavItem href="/macro/global" label="Global Macro" count={9} />
        <NavItem href="/macro/geopolitics" label="Geopolitics" count={3} />
      </div>

      <SidebarFoot />
    </aside>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="px-3 pb-2 pt-1 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-fg-3">
      {children}
    </div>
  );
}

function NavItem({
  href, icon: Icon, label, count, dot, active,
}: { href: string; icon?: any; label: string; count?: number; dot?: string; active?: boolean }) {
  return (
    <Link
      href={href}
      className={`relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] transition
        ${active ? "bg-accent-soft text-fg-0" : "text-fg-1 hover:bg-bg-2 hover:text-fg-0"}`}
    >
      {active && (
        <span className="absolute -left-3 top-2 bottom-2 w-0.5 rounded-sm bg-accent shadow-[0_0_12px_var(--accent)]" />
      )}
      {Icon && <Icon className="size-3.5" />}
      {dot && <span className="size-2 rounded-sm" style={{ background: dot }} />}
      <span>{label}</span>
      {typeof count === "number" && (
        <span className={`ml-auto mono text-[11.5px] ${active ? "text-accent" : "text-fg-3"}`}>{count}</span>
      )}
    </Link>
  );
}

function SidebarFoot() {
  return (
    <div className="mt-auto rounded-md border border-line-1 bg-bg-1 p-3 text-xs">
      <Row label="Vault" value="1,284 files" />
      <Row label="Queue" value="3 jobs" />
      <Row label="Pipeline" value={<span className="text-pos">healthy</span>} />
      <Row label="DLQ" value="0" />
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 py-0.5">
      <span className="text-fg-2">{label}</span>
      <span className="flex-1" />
      <span className="mono text-fg-1">{value}</span>
    </div>
  );
}
