import express from "express";
import pino from "pino";
import pinoHttp from "pino-http";
import { z } from "zod";
import { renderMasterReport } from "./templates/master-report.js";
import { renderDailyBrief } from "./templates/daily-brief.js";
import { uploadToSupabase } from "./storage.js";

const log = pino({ name: "pdf-engine" });
const app = express();
app.use(express.json({ limit: "10mb" }));
app.use(pinoHttp({ logger: log }));

app.get("/healthz", (_req, res) => res.json({ status: "ok" }));

const RenderBody = z.object({
  template: z.enum(["master-report", "daily-brief", "weekly-digest"]),
  data: z.object({
    body_md: z.string().optional(),
    report_id: z.string().optional(),
    date: z.string().optional(),
    title: z.string().optional(),
  }).passthrough(),
  options: z
    .object({
      upload: z.boolean().default(true),
      filename: z.string().optional(),
    })
    .default({}),
});

app.post("/render", async (req, res) => {
  const parsed = RenderBody.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  const { template, data, options } = parsed.data;
  try {
    let pdfBuffer: Buffer;
    switch (template) {
      case "master-report":
        pdfBuffer = await renderMasterReport(data);
        break;
      case "daily-brief":
        pdfBuffer = await renderDailyBrief(data);
        break;
      default:
        return res.status(400).json({ error: `unsupported template: ${template}` });
    }

    if (!options.upload) {
      return res.json({ pdfBytes: pdfBuffer.toString("base64") });
    }

    const filename =
      options.filename ?? `reports/${data.date ?? new Date().toISOString().slice(0, 10)}-${template}.pdf`;
    const url = await uploadToSupabase(filename, pdfBuffer);
    return res.json({ url, filename });
  } catch (err: any) {
    log.error({ err }, "render.failed");
    return res.status(500).json({ error: err.message });
  }
});

const port = Number(process.env.PORT ?? 4000);
app.listen(port, () => log.info({ port }, "pdf-engine.listening"));
