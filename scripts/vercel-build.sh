#!/usr/bin/env bash
# Vercel build hook: refresh apps/dashboard/data/ from generated/
# Called by vercel.json "buildCommand". Static deploy — no compilation.

set -u  # error on undefined vars; do NOT use -e (we tolerate missing source files)

mkdir -p apps/dashboard/data

cp -f generated/index.json            apps/dashboard/data/index.json            2>/dev/null || true
cp -f generated/search-index.json     apps/dashboard/data/search-index.json     2>/dev/null || true
cp -f generated/graph.json            apps/dashboard/data/graph.json            2>/dev/null || true
cp -f generated/embeddings-ready.json apps/dashboard/data/embeddings-ready.json 2>/dev/null || true

echo "Vercel build: apps/dashboard/data/ refreshed"
ls -la apps/dashboard/data/ 2>/dev/null || true
