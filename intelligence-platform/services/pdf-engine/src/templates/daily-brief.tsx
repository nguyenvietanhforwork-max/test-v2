/** Single-bucket daily brief, simpler layout than master report. */
import React from "react";
import { Document, Page, Text, View, StyleSheet, pdf } from "@react-pdf/renderer";

const s = StyleSheet.create({
  page: { fontFamily: "Helvetica", fontSize: 10.5, padding: 48, color: "#111" },
  h1: { fontSize: 20, fontWeight: 700, marginBottom: 8 },
  meta: { fontSize: 9, color: "#666", marginBottom: 18 },
  p: { lineHeight: 1.5, marginBottom: 6 },
});

export async function renderDailyBrief(data: { body_md?: string; title?: string; date?: string }): Promise<Buffer> {
  const doc = (
    <Document>
      <Page size="A4" style={s.page}>
        <Text style={s.h1}>{data.title ?? "Daily Brief"}</Text>
        <Text style={s.meta}>{data.date ?? new Date().toISOString().slice(0, 10)}</Text>
        {(data.body_md ?? "").split("\n\n").map((para, i) => (
          <Text key={i} style={s.p}>{para}</Text>
        ))}
      </Page>
    </Document>
  );
  const stream = await pdf(doc).toBuffer();
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    stream.on("data", (c) => chunks.push(c as Buffer));
    stream.on("end", () => resolve(Buffer.concat(chunks)));
    stream.on("error", reject);
  });
}
