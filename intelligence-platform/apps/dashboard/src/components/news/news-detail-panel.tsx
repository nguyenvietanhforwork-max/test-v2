"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ExternalLink, FileText, Folder, BookOpen, X } from "lucide-react";
import { useNewsDetail, useTraceBack } from "@/hooks/use-news";

export function NewsDetailPanel({ id, onClose }: { id: string | null; onClose: () => void }) {
  const { data: item } = useNewsDetail(id);
  const { data: trace } = useTraceBack(id);

  return (
    <AnimatePresence>
      {id && (
        <motion.aside
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", stiffness: 180, damping: 22 }}
          className="fixed top-0 right-0 h-full w-[520px] z-40 glass border-l border-border-subtle p-6 overflow-y-auto"
        >
          <div className="flex justify-between items-start mb-4">
            <div className="text-[10px] tracking-ultra text-accent-gold">NEWS DETAIL</div>
            <button onClick={onClose} className="p-1 rounded hover:bg-glass-hover">
              <X className="h-4 w-4" />
            </button>
          </div>

          {!item ? (
            <div className="text-ink-dim text-sm">Loading…</div>
          ) : (
            <>
              <h3 className="font-editorial text-2xl leading-tight">{item.title}</h3>
              {item.summary?.thesis && (
                <p className="mt-4 text-ink-muted leading-relaxed">{item.summary.thesis}</p>
              )}

              {item.summary?.supporting_points?.length > 0 && (
                <div className="mt-5">
                  <div className="text-[10px] tracking-ultra text-accent-gold mb-2">KEY POINTS</div>
                  <ul className="space-y-2 text-sm">
                    {item.summary.supporting_points.map((p: any, i: number) => (
                      <li key={i} className="flex gap-2.5">
                        <span className="text-accent-gold/70 num text-xs mt-0.5">{i + 1}</span>
                        <span>{p.text}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {item.summary?.implications?.length > 0 && (
                <div className="mt-5">
                  <div className="text-[10px] tracking-ultra text-accent-gold mb-2">IMPLICATIONS</div>
                  <ul className="space-y-2 text-sm">
                    {item.summary.implications.map((p: any, i: number) => (
                      <li key={i} className="text-ink-muted">{p.text}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mt-6 pt-5 border-t border-border-subtle space-y-2">
                <div className="text-[10px] tracking-ultra text-accent-gold mb-1">TRACE-BACK</div>
                {item.source_url && (
                  <TraceLink href={item.source_url} icon={ExternalLink} label="Open original source" />
                )}
                {trace?.obsidian_uri && (
                  <TraceLink href={trace.obsidian_uri} icon={Folder} label="Open in vault" />
                )}
                {trace?.report_ids?.[0] && (
                  <TraceLink
                    href={`/reports/${trace.report_ids[0]}`}
                    icon={FileText}
                    label="Open generated report"
                    internal
                  />
                )}
                {trace?.related_wiki_slugs?.length > 0 && (
                  <div className="pt-2">
                    <div className="text-xs text-ink-dim mb-1.5">Related wiki</div>
                    <div className="flex flex-wrap gap-1.5">
                      {trace.related_wiki_slugs.map((s: string) => (
                        <a key={s} href={`/wiki/${s}`} className="chip">
                          <BookOpen className="h-3 w-3" />
                          {s}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

function TraceLink({
  href,
  icon: Icon,
  label,
  internal,
}: {
  href: string;
  icon: any;
  label: string;
  internal?: boolean;
}) {
  return (
    <a
      href={href}
      target={internal ? "_self" : "_blank"}
      rel={internal ? undefined : "noopener noreferrer"}
      className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border-subtle bg-glass glass-hover text-sm"
    >
      <Icon className="h-3.5 w-3.5 text-accent-signal" />
      <span>{label}</span>
    </a>
  );
}
