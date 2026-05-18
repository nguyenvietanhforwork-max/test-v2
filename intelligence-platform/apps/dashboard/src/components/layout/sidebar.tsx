"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Calendar, FileText, Network, Search, Settings, BookOpen } from "lucide-react";
import { cn } from "@/lib/cn";

const NAV = [
  { href: "/", label: "Daily", icon: Calendar },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/search", label: "Search", icon: Search },
  { href: "/graph", label: "Graph", icon: Network },
  { href: "/wiki", label: "Wiki", icon: BookOpen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-60 shrink-0 border-r border-border-subtle bg-glass backdrop-blur-glass">
      <div className="h-16 flex items-center px-6">
        <div className="text-ink-primary font-editorial text-lg tracking-tight">Intelligence</div>
        <div className="ml-2 text-[10px] tracking-ultra text-ink-muted">v0.1</div>
      </div>
      <nav className="px-3 mt-2 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                active
                  ? "bg-glass-hover text-ink-primary"
                  : "text-ink-muted hover:bg-glass hover:text-ink-primary",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
