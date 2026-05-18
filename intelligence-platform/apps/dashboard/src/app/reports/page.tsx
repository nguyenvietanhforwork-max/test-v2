import { ReportCenter } from "@/components/reports/report-center";
import { fetchReports } from "@/lib/api";

export default async function ReportsPage() {
  const reports = await fetchReports();
  return <ReportCenter initial={reports} />;
}
