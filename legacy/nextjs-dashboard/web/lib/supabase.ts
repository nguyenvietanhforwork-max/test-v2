"use client";

/**
 * Supabase client — used for Realtime row subscriptions on `news_item` and `report`.
 *
 * When NEXT_PUBLIC_SUPABASE_URL is unset we export a null client and the
 * WebSocketProvider falls back to its native ws:// connection to the FastAPI
 * gateway. This means the dashboard works in three modes:
 *
 *   1. Pure mocks                — no backend, no Supabase
 *   2. FastAPI WebSocket         — backend live, no Supabase
 *   3. Supabase Realtime + REST  — Supabase live, optional FastAPI for write paths
 */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

export const supabase: SupabaseClient | null =
  URL && ANON_KEY
    ? createClient(URL, ANON_KEY, {
        realtime: { params: { eventsPerSecond: 10 } },
        auth: { persistSession: true, autoRefreshToken: true },
      })
    : null;

/** Subscribe to INSERTs on news_item — fires the dashboard's "new card" animation. */
export function subscribeNews(onInsert: (row: any) => void) {
  if (!supabase) return () => {};
  const channel = supabase
    .channel("news-changes")
    .on(
      "postgres_changes",
      { event: "INSERT", schema: "public", table: "news_item" },
      (payload) => onInsert(payload.new),
    )
    .subscribe();
  return () => {
    supabase.removeChannel(channel);
  };
}

/** Subscribe to INSERTs on report — fires the toast + report center refresh. */
export function subscribeReports(onInsert: (row: any) => void) {
  if (!supabase) return () => {};
  const channel = supabase
    .channel("report-changes")
    .on(
      "postgres_changes",
      { event: "INSERT", schema: "public", table: "report" },
      (payload) => onInsert(payload.new),
    )
    .subscribe();
  return () => {
    supabase.removeChannel(channel);
  };
}
