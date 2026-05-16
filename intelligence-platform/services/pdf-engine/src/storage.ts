import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.SUPABASE_URL ?? "",
  process.env.SUPABASE_SERVICE_ROLE_KEY ?? "",
);

const BUCKET = process.env.SUPABASE_REPORTS_BUCKET ?? "reports";

export async function uploadToSupabase(filename: string, body: Buffer): Promise<string> {
  if (!process.env.SUPABASE_URL) {
    // dev fallback: data URL
    return `data:application/pdf;base64,${body.toString("base64")}`;
  }
  const { error } = await supabase.storage
    .from(BUCKET)
    .upload(filename, body, { contentType: "application/pdf", upsert: true });
  if (error) throw error;
  const { data } = await supabase.storage
    .from(BUCKET)
    .createSignedUrl(filename, 60 * 15); // 15 min
  if (!data) throw new Error("could not sign URL");
  return data.signedUrl;
}
