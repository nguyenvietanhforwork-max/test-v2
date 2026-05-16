"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchNewsDetail, fetchTraceBack } from "@/lib/api";

export function useNewsDetail(id: string | null) {
  return useQuery({
    queryKey: ["news", id],
    queryFn: () => (id ? fetchNewsDetail(id) : Promise.resolve(null)),
    enabled: !!id,
  });
}

export function useTraceBack(id: string | null) {
  return useQuery({
    queryKey: ["trace", id],
    queryFn: () => (id ? fetchTraceBack(id) : Promise.resolve(null)),
    enabled: !!id,
  });
}
