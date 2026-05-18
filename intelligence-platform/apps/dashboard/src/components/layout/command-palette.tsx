"use client";

import { Command } from "cmdk";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <>
      <button onClick={() => setOpen(true)} className="chip">
        <Search className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Search</span>
        <kbd className="hidden sm:inline ml-2 text-[10px] text-ink-dim">⌘K</kbd>
      </button>
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/60 backdrop-blur-sm" onClick={() => setOpen(false)}>
          <div className="glass w-[560px] rounded-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <Command label="Global search">
              <Command.Input
                placeholder="Search news, companies, industries…"
                className="w-full bg-transparent px-5 py-4 outline-none text-ink-primary placeholder:text-ink-dim border-b border-border-subtle"
              />
              <Command.List className="max-h-80 overflow-y-auto p-2">
                <Command.Item
                  onSelect={() => {
                    router.push("/search");
                    setOpen(false);
                  }}
                  className="px-3 py-2 rounded-md cursor-pointer hover:bg-glass-hover text-sm"
                >
                  Open full search
                </Command.Item>
              </Command.List>
            </Command>
          </div>
        </div>
      )}
    </>
  );
}
