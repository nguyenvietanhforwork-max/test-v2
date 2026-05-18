import { Suspense } from "react";
import { DailyBriefHeader } from "@/components/dashboard/DailyBriefHeader";
import { IndustryHeatmap } from "@/components/dashboard/IndustryHeatmap";
import { IntelligenceFeed } from "@/components/dashboard/IntelligenceFeed";
import { FilterChips } from "@/components/dashboard/FilterChips";
import { FeedSkeleton } from "@/components/dashboard/FeedSkeleton";
import { getDailyBrief, getIndustryHeatmap, getNewsFeed } from "@/lib/api";

export const revalidate = 60;

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ industry?: string; region?: string; bucket?: string; q?: string }>;
}) {
  const filters = await searchParams;
  const [brief, heatmap] = await Promise.all([
    getDailyBrief(),
    getIndustryHeatmap({ window: "1d" }),
  ]);

  return (
    <>
      <DailyBriefHeader brief={brief} />

      <section className="mt-10">
        <SectionHead title="Industry Heatmap" subtitle={`${heatmap.cells.length} sectors · today`} />
        <IndustryHeatmap data={heatmap} />
      </section>

      <section className="mt-10">
        <SectionHead title="Intelligence Feed" subtitle="Filtered" />
        <FilterChips current={filters} />
        <Suspense fallback={<FeedSkeleton />}>
          <FeedAsync params={filters} />
        </Suspense>
      </section>
    </>
  );
}

async function FeedAsync({ params }: { params: Record<string, string | undefined> }) {
  const feed = await getNewsFeed(params);
  return <IntelligenceFeed items={feed.items} />;
}

function SectionHead({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4 flex items-end gap-3">
      <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      {subtitle && <span className="mono text-xs text-fg-3">{subtitle}</span>}
      <div className="mx-2 h-px flex-1 self-center bg-line-1" />
    </div>
  );
}
