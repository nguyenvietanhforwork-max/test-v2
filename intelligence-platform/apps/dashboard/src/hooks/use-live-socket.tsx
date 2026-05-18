"use client";

import { createContext, useContext, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { create } from "zustand";

type LiveState = {
  lastEvent: { type: string; data: any; ts: number } | null;
  push: (e: { type: string; data: any }) => void;
};

export const useLiveStore = create<LiveState>((set) => ({
  lastEvent: null,
  push: (e) => set({ lastEvent: { ...e, ts: Date.now() } }),
}));

const Ctx = createContext<null>(null);

export function LiveSocketProvider({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient();
  const ref = useRef<WebSocket | null>(null);

  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws";
    let retries = 0;
    let stopped = false;

    function connect() {
      const ws = new WebSocket(`${url}?channels=news,reports`);
      ref.current = ws;
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          useLiveStore.getState().push(msg);
          if (msg.type === "news.ingested" || msg.type === "news.classified") {
            qc.invalidateQueries({ queryKey: ["dashboard"] });
          }
          if (msg.type === "report.ready" || msg.type === "pdf.ready") {
            qc.invalidateQueries({ queryKey: ["reports"] });
          }
        } catch {}
      };
      ws.onclose = () => {
        if (stopped) return;
        retries++;
        setTimeout(connect, Math.min(1000 * 2 ** retries, 15000));
      };
    }
    connect();
    return () => {
      stopped = true;
      ref.current?.close();
    };
  }, [qc]);

  return <Ctx.Provider value={null}>{children}</Ctx.Provider>;
}

export function useLiveSocket() {
  return useContext(Ctx);
}
