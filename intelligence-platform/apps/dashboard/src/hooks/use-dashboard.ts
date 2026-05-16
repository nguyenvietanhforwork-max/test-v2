"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchDashboardToday } from "@/lib/api";

export function useDashboardToday(date?: string, initialData?: any) {
  return useQuery({
    queryKey: ["dashboard", date ?? "today"],
    queryFn: () => fetchDashboardToday(date),
    initialData,
    refetchInterval: 60_000,
  });
}
