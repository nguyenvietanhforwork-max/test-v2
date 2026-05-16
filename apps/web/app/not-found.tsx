import Link from "next/link";

export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center px-6">
      <div className="text-center">
        <div className="mono mb-3 text-[11px] uppercase tracking-[0.2em] text-fg-3">Atlas · 404</div>
        <h1 className="text-3xl font-semibold tracking-tight">No record matches that path.</h1>
        <p className="mt-2 text-fg-2">The vault has no clipping, report, or entity at this address.</p>
        <Link href="/" className="mono mt-6 inline-block rounded-md border border-accent-line bg-accent-soft px-3 py-2 text-sm text-accent">
          ← back to dashboard
        </Link>
      </div>
    </div>
  );
}
