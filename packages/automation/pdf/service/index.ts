/**
 * Atlas PDF microservice — Puppeteer-based markdown → institutional PDF.
 *
 * Endpoints:
 *   POST /render        { markdown, filename } → { object_key }
 *   GET  /reports/:id.pdf  → application/pdf stream
 *
 * Run: pnpm dev (port 4000)
 */

import express from "express";
import puppeteer from "puppeteer";
import { marked } from "marked";
import { createHash } from "crypto";
import { Client as MinioClient } from "minio";

const app = express();
app.use(express.json({ limit: "10mb" }));

const STORAGE_BACKEND = process.env.STORAGE_BACKEND ?? "minio";
const BUCKET = process.env.MINIO_BUCKET ?? "atlas-pdfs";
const SUPABASE_BUCKET = process.env.SUPABASE_STORAGE_BUCKET ?? "atlas-pdfs";

let minio: MinioClient | null = null;
function getMinio() {
  if (!minio) {
    minio = new MinioClient({
      endPoint: process.env.MINIO_ENDPOINT?.split(":")[0] ?? "minio",
      port: Number(process.env.MINIO_ENDPOINT?.split(":")[1] ?? 9000),
      useSSL: process.env.MINIO_SECURE === "true",
      accessKey: process.env.MINIO_ACCESS_KEY!,
      secretKey: process.env.MINIO_SECRET_KEY!,
    });
  }
  return minio;
}

let browserPromise: Promise<puppeteer.Browser> | null = null;
const getBrowser = () => (browserPromise ??= puppeteer.launch({ args: ["--no-sandbox"], headless: true }));

const STYLE = `
  @page { size: A4; margin: 24mm 20mm; }
  * { box-sizing: border-box; }
  body {
    font-family: "Inter", "Helvetica Neue", sans-serif;
    color: #0B0C10; font-size: 11pt; line-height: 1.55;
  }
  h1 { font-size: 22pt; letter-spacing: -0.02em; margin: 0 0 4mm; }
  h2 { font-size: 14pt; letter-spacing: -0.01em; margin: 6mm 0 2mm; padding-bottom: 1mm; border-bottom: 1px solid #ccc; }
  h3 { font-size: 11.5pt; font-weight: 600; margin: 4mm 0 1mm; }
  blockquote { border-left: 3px solid #B4810B; margin: 0; padding-left: 4mm; color: #2E3340; }
  ul { margin: 1mm 0 1mm 5mm; padding: 0; }
  li { margin: 0.5mm 0; }
  .footer { font-size: 8pt; color: #6C7488; text-align: right; }
`;

app.post("/render", async (req, res) => {
  try {
    const { markdown, filename } = req.body as { markdown: string; filename: string };
    const html = `<!doctype html><meta charset="utf-8"><style>${STYLE}</style><div>${marked.parse(markdown)}</div>`;
    const browser = await getBrowser();
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: "networkidle0" });
    const pdf = await page.pdf({ format: "A4", printBackground: true });
    await page.close();

    const objectKey = `${new Date().toISOString().slice(0, 10)}/${filename}`;
    const buffer = Buffer.from(pdf);
    const etag = createHash("sha256").update(buffer).digest("hex").slice(0, 16);
    await uploadPdf(objectKey, buffer);
    res.json({ object_key: objectKey, etag, bytes: buffer.length });
  } catch (e) {
    res.status(500).json({ error: (e as Error).message });
  }
});

app.get("/reports/:id.pdf", async (req, res) => {
  try {
    const stream = await getMinio().getObject(BUCKET, req.params.id + ".pdf");
    res.setHeader("Content-Type", "application/pdf");
    stream.pipe(res);
  } catch (e) {
    res.status(404).end();
  }
});

app.get("/healthz", (_, r) => r.json({ ok: true }));

app.listen(4000, () => console.log("pdf service listening on :4000"));

async function uploadPdf(objectKey: string, buffer: Buffer) {
  if (STORAGE_BACKEND === "supabase") {
    const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, "");
    const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;
    if (!supabaseUrl || !serviceKey) {
      throw new Error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for Supabase Storage");
    }

    const response = await fetch(`${supabaseUrl}/storage/v1/object/${SUPABASE_BUCKET}/${objectKey}`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${serviceKey}`,
        "apikey": serviceKey,
        "Content-Type": "application/pdf",
        "x-upsert": "true",
      },
      body: buffer,
    });
    if (!response.ok) {
      throw new Error(`Supabase upload failed: ${response.status} ${await response.text()}`);
    }
    return;
  }

  const client = getMinio();
  if (!(await client.bucketExists(BUCKET))) await client.makeBucket(BUCKET);
  await client.putObject(BUCKET, objectKey, buffer, buffer.length, { "Content-Type": "application/pdf" });
}
