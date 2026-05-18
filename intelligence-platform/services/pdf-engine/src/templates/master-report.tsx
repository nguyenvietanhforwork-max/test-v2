/**
 * Institutional master report — React-PDF for deterministic typography.
 * Cover + executive thesis + sections (one per bucket) + sources.
 */
import React from "react";
import { Document, Page, Text, View, StyleSheet, pdf, Font } from "@react-pdf/renderer";
import { marked } from "marked";

const styles = StyleSheet.create({
  page: {
    fontFamily: "Helvetica",
    fontSize: 10.5,
    padding: 56,
    color: "#111111",
    backgroundColor: "#FFFFFF",
  },
  cover: {
    flexDirection: "column",
    justifyContent: "center",
    flex: 1,
  },
  brand: { fontSize: 9, letterSpacing: 4, color: "#666666", marginBottom: 14 },
  title: { fontSize: 28, fontWeight: 700, lineHeight: 1.15 },
  date: { fontSize: 11, marginTop: 18, color: "#444" },
  h1: { fontSize: 16, fontWeight: 700, marginTop: 20, marginBottom: 8 },
  h2: { fontSize: 13, fontWeight: 700, marginTop: 14, marginBottom: 6 },
  h3: { fontSize: 11, fontWeight: 700, marginTop: 10, marginBottom: 4 },
  p: { lineHeight: 1.5, marginBottom: 6 },
  bullet: { flexDirection: "row", marginBottom: 4 },
  bulletDot: { width: 10, fontSize: 10 },
  hr: { borderBottomWidth: 0.5, borderBottomColor: "#E0E0E0", marginVertical: 10 },
  footer: { position: "absolute", bottom: 24, left: 56, right: 56, fontSize: 8, color: "#999" },
});

function mdToBlocks(md: string): { type: string; text: string }[] {
  // Minimal markdown → block array. For production swap in unified+remark.
  const blocks: { type: string; text: string }[] = [];
  const tokens = marked.lexer(md);
  for (const t of tokens) {
    if (t.type === "heading") blocks.push({ type: `h${(t as any).depth}`, text: (t as any).text });
    else if (t.type === "paragraph") blocks.push({ type: "p", text: (t as any).text });
    else if (t.type === "list") {
      for (const item of (t as any).items) blocks.push({ type: "li", text: item.text });
    } else if (t.type === "hr") blocks.push({ type: "hr", text: "" });
  }
  return blocks;
}

function MasterReportDoc({ body_md, date }: { body_md: string; date?: string }) {
  const blocks = mdToBlocks(body_md);
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <View style={styles.cover}>
          <Text style={styles.brand}>INTELLIGENCE — DAILY BRIEF</Text>
          <Text style={styles.title}>Master Report</Text>
          <Text style={styles.date}>{date ?? new Date().toISOString().slice(0, 10)}</Text>
        </View>
        <Text style={styles.footer}>Confidential — for internal research use only.</Text>
      </Page>
      <Page size="A4" style={styles.page} wrap>
        {blocks.map((b, i) => {
          if (b.type === "h1") return <Text key={i} style={styles.h1}>{b.text}</Text>;
          if (b.type === "h2") return <Text key={i} style={styles.h2}>{b.text}</Text>;
          if (b.type === "h3") return <Text key={i} style={styles.h3}>{b.text}</Text>;
          if (b.type === "li")
            return (
              <View key={i} style={styles.bullet}>
                <Text style={styles.bulletDot}>•</Text>
                <Text style={{ flex: 1 }}>{b.text}</Text>
              </View>
            );
          if (b.type === "hr") return <View key={i} style={styles.hr} />;
          return <Text key={i} style={styles.p}>{b.text}</Text>;
        })}
        <Text style={styles.footer} render={({ pageNumber, totalPages }) => `${pageNumber} / ${totalPages}`} fixed />
      </Page>
    </Document>
  );
}

export async function renderMasterReport(data: { body_md?: string; date?: string }): Promise<Buffer> {
  const doc = <MasterReportDoc body_md={data.body_md ?? ""} date={data.date} />;
  const stream = await pdf(doc).toBuffer();
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    stream.on("data", (c) => chunks.push(c as Buffer));
    stream.on("end", () => resolve(Buffer.concat(chunks)));
    stream.on("error", reject);
  });
}
