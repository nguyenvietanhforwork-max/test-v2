import { DailyView } from "@/components/news/daily-view";
import { fetchDashboardToday } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const data = await fetchDashboardToday();
  return <DailyView initialData={data} />;
}
