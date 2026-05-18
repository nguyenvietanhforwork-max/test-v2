"use client";

import { RefreshCw, Loader2 } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";
import { triggerRefresh } from "@/lib/api";
import { DateScrubber } from "./date-scrubber";
import { CommandPalette } from "./command-palette";

export function TopBar() {
  const [refreshing, setRefreshing] = useState(false);
  async function onRefresh() {
    setRefreshing(true);
    try {
      await triggerRefresh();
    } finally {
      setTimeout(() => setRefreshing(false), 800);
    }
  }
  return (
    <div className="h-16 border-b border-border-subtle bg-canvas/60 backdrop-blur-glass">
      <div className="flex items-center justify-between px-8 h-full">
        <DateScrubber />
        <div className="flex items-center gap-3">
          <CommandPalette />
          <motion.button
            onClick={onRefresh}
            whileTap={{ scale: 0.96 }}
            className="chip text-ink-primary hover:bg-glass-hover"
            aria-label="Refresh vault"
          >
            {refreshing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5" />
            )}
            <span>Refresh</span>
          </motion.button>
        </div>
      </div>
    </div>
  );
}
