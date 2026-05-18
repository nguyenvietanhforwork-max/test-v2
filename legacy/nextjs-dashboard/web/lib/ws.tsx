"use client";

import { createContext, useContext, useEffect, useRef } from "react";
import type { WebSocketEvent } from "./types";
import { subscribeNews, subscribeReports } from "./supabase";

type Listener = (event: WebSocketEvent) => void;

interface WS {
  subscribe(fn: Listener): () => void;
  send(msg: unknown): void;
}

const Ctx = createContext<WS | null>(null);

export function useWebSocket(): WS {
  return useContext(Ctx) ?? { subscribe: () => () => {}, send: () => {} };
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const listeners = useRef<Set<Listener>>(new Set());
  const sockRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const url = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/stream");
    let s: WebSocket | null = null;
    let backoff = 1000;
    let killed = false;

    const connect = () => {
      try {
        s = new WebSocket(url);
        sockRef.current = s;
        s.onmessage = (e) => {
          try {
            const evt = JSON.parse(e.data) as WebSocketEvent;
            listeners.current.forEach((fn) => fn(evt));
          } catch { /* ignore */ }
        };
        s.onopen = () => { backoff = 1000; };
        s.onclose = () => {
          if (killed) return;
          setTimeout(connect, backoff);
          backoff = Math.min(backoff * 2, 30_000);
        };
        s.onerror = () => s?.close();
      } catch {
        setTimeout(connect, backoff);
      }
    };
    connect();
    const offNews = subscribeNews((row) => {
      listeners.current.forEach((fn) => fn({ type: "news.created", payload: row } as WebSocketEvent));
    });
    const offReports = subscribeReports((row) => {
      listeners.current.forEach((fn) => fn({ type: "report.published", payload: row } as WebSocketEvent));
    });
    return () => {
      killed = true;
      s?.close();
      offNews();
      offReports();
    };
  }, []);

  const value: WS = {
    subscribe(fn) { listeners.current.add(fn); return () => listeners.current.delete(fn); },
    send(msg) { sockRef.current?.send(JSON.stringify(msg)); },
  };

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
