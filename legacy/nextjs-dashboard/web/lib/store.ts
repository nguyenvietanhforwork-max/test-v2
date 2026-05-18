import { create } from "zustand";
import type { NewsItem } from "./types";

interface AppState {
  filters: { industry?: string; region?: string; bucket?: string; q?: string };
  setFilter: (k: keyof AppState["filters"], v?: string) => void;
  resetFilters: () => void;

  // Realtime overlay
  liveNews: NewsItem[];          // arrived via WS, oldest at end
  pushLive: (n: NewsItem) => void;
  clearLive: () => void;

  // UI
  cmdOpen: boolean;
  setCmdOpen: (b: boolean) => void;
}

export const useApp = create<AppState>((set) => ({
  filters: {},
  setFilter: (k, v) => set((s) => ({ filters: { ...s.filters, [k]: v } })),
  resetFilters: () => set({ filters: {} }),

  liveNews: [],
  pushLive: (n) => set((s) => ({ liveNews: [n, ...s.liveNews].slice(0, 64) })),
  clearLive: () => set({ liveNews: [] }),

  cmdOpen: false,
  setCmdOpen: (b) => set({ cmdOpen: b }),
}));
