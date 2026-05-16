import { ReportViewer } from "@/components/reports/report-viewer";
import { fetchReport } from "@/lib/api";

export default async function ReportDetailPage({ params }: { params: { id: string } }) {
  const report = await fetchReport(params.id);
  return <ReportViewer report={report} />;
}
