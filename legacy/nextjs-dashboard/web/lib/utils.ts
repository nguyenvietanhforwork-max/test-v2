import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function groupBy<T>(arr: T[], key: (item: T) => string): Record<string, T[]> {
  return arr.reduce((acc, item) => {
    const k = key(item);
    (acc[k] ||= []).push(item);
    return acc;
  }, {} as Record<string, T[]>);
}

export function formatVND(n: number): string {
  return new Intl.NumberFormat("vi-VN").format(n);
}

export function formatPercent(n: number, withSign = true): string {
  const s = withSign && n > 0 ? "+" : "";
  return `${s}${n.toFixed(2)}%`;
}
