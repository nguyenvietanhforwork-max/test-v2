import { TopBar } from "@/components/shell/TopBar";
import { Sidebar } from "@/components/shell/Sidebar";
import { RightRail } from "@/components/shell/RightRail";
import { PipelineStatusBar } from "@/components/dashboard/PipelineStatusBar";
import { CommandPalette } from "@/components/search/CommandPalette";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen grid-cols-1 grid-rows-[auto_1fr] lg:h-screen lg:grid-cols-[240px_1fr] xl:grid-cols-[240px_1fr_320px] xl:grid-rows-[56px_1fr]">
      <TopBar />
      <Sidebar />
      <main className="overflow-y-auto bg-bg-0 px-4 pb-32 pt-5 md:px-8 md:pt-7">
        {children}
      </main>
      <RightRail />
      <PipelineStatusBar />
      <CommandPalette />
    </div>
  );
}
