import { DailyView } from "@/components/news/daily-view";
import { fetchDashboardToday } from "@/lib/api";

export default async function DailyDatePage({ params }: { params: { date: string } }) {
  const data = await fetchDashboardToday(params.date);
  return <DailyView initialData={data} date={params.date} />;
}
