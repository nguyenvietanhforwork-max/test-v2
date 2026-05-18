import { getReport } from "@/lib/api";
import { ReportViewer } from "@/components/report/ReportViewer";

export default async function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const report = await getReport(id);
  return <ReportViewer report={report} />;
}
