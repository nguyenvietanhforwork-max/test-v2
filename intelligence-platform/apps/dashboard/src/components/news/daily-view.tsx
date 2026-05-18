"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { useDashboardToday } from "@/hooks/use-dashboard";
import { Headline } from "./headline";
import { BucketCard } from "./bucket-card";
import { NewsDetailPanel } from "./news-detail-panel";
import { FilterDock } from "./filter-dock";

export function DailyView({ initialData, date }: { initialData: any; date?: string }) {
  const { data } = useDashboardToday(date, initialData);
  const [openItemId, setOpenItemId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <Headline data={data.headline} />
      <FilterDock />

      <motion.div
        className="grid grid-cols-1 lg:grid-cols-2 gap-4"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <BucketCard
          bucket="vn_corp"
          title="Vietnam — Corporates"
          payload={data.buckets.vn_corp}
          items={data.recent_items}
          onOpen={setOpenItemId}
        />
        <BucketCard
          bucket="intl_corp"
          title="International — Corporates"
          payload={data.buckets.intl_corp}
          items={data.recent_items}
          onOpen={setOpenItemId}
        />
        <BucketCard
          bucket="vn_macro"
          title="Vietnam — Macro"
          payload={data.buckets.vn_macro}
          items={data.recent_items}
          onOpen={setOpenItemId}
        />
        <BucketCard
          bucket="intl_macro"
          title="International — Macro"
          payload={data.buckets.intl_macro}
          items={data.recent_items}
          onOpen={setOpenItemId}
        />
      </motion.div>

      <NewsDetailPanel id={openItemId} onClose={() => setOpenItemId(null)} />
    </div>
  );
}
