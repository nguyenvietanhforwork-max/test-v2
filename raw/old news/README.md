# raw/old news — Archive

Daily archive of fully-processed source files.

Structure:
```
old news/
├── 2026-05-14/         ← news files processed on this date
│   ├── social/         ← social posts processed on this date
│   └── pdf/            ← PDFs processed on this date
└── 2026-05-15/
    └── ...
```

**Rules (AGENTS.md §9):**
- The agent only moves a file here after ALL of: news report, social/pdf report (if applicable), MASTER report, news_database.json update have succeeded.
- Original filenames, mtimes, and metadata are preserved.
- Once moved, files are still immutable. They are never re-processed.
