import type { Industry } from "./types";

export const INDUSTRIES: Industry[] = [
  { slug: "banking",          name: "Banking",          color: "var(--cyan)",        todayCount: 8 },
  { slug: "real-estate",      name: "Real Estate",      color: "var(--accent)",       todayCount: 5 },
  { slug: "technology",       name: "Technology",       color: "var(--violet)",       todayCount: 4 },
  { slug: "energy",           name: "Energy",           color: "#F59E0B",             todayCount: 3 },
  { slug: "pharma",           name: "Pharmaceutical",   color: "#4ADE80",             todayCount: 1 },
  { slug: "automotive",       name: "Automotive",       color: "#F87171",             todayCount: 2 },
  { slug: "retail",           name: "Retail",           color: "#FB923C" },
  { slug: "steel",            name: "Steel",            color: "#94A3B8",             todayCount: 2 },
  { slug: "securities",       name: "Securities",       color: "#2DD4BF" },
  { slug: "manufacturing",    name: "Manufacturing",    color: "#A78BFA" },
  { slug: "logistics",        name: "Logistics",        color: "#38BDF8" },
  { slug: "agriculture",      name: "Agriculture",      color: "#84CC16" },
  { slug: "construction",     name: "Construction",     color: "#FACC15" },
  { slug: "utilities",        name: "Utilities",        color: "#60A5FA" },
  { slug: "aviation",         name: "Aviation",         color: "#C084FC" },
  { slug: "fnb",              name: "F&B",              color: "#F472B6" },
  { slug: "insurance",        name: "Insurance",        color: "#22D3EE" },
  { slug: "chemicals",        name: "Chemicals",        color: "#FB7185" },
  { slug: "textiles",         name: "Textiles",         color: "#E879F9" },
  { slug: "mining",           name: "Mining",           color: "#D4D4D8" },
  { slug: "telecom",          name: "Telecom",          color: "#818CF8" },
  { slug: "shipping",         name: "Shipping",         color: "#4FD1C5" },
  { slug: "healthcare",       name: "Healthcare",       color: "#34D399" },
  { slug: "education",        name: "Education",        color: "#FCD34D" },
  { slug: "fisheries",        name: "Fisheries",        color: "#67E8F9" },
  { slug: "industrial-parks", name: "Industrial Parks", color: "#FDE047" },
  { slug: "consumer-goods",   name: "Consumer Goods",   color: "#F0ABFC" },
  { slug: "other",            name: "Other",            color: "#A1A1AA" },
];

export const INDUSTRY_MAP = Object.fromEntries(INDUSTRIES.map((i) => [i.slug, i]));
