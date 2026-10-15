"""SQLite schema from SPEC §4. The database is local and gitignored (full texts stay local)."""

import sqlite3
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS acordao (
  doc_id TEXT PRIMARY KEY,
  processo TEXT NOT NULL,
  url TEXT NOT NULL,
  secao TEXT,
  relator TEXT,
  data_iso TEXT,
  descritores_json TEXT,
  meio_processual TEXT,
  decisao TEXT,
  sumario TEXT,
  texto TEXT,
  texto_sha256 TEXT,
  fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS classification (
  doc_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  relevant INTEGER NOT NULL,
  position_id TEXT,
  quote TEXT,
  quote_ok INTEGER NOT NULL DEFAULT 0,
  note TEXT,
  text_source TEXT,
  model TEXT,
  prompt_version TEXT,
  created_at TEXT,
  PRIMARY KEY (doc_id, question_id)
);
CREATE INDEX IF NOT EXISTS idx_acordao_processo ON acordao(processo);
CREATE TABLE IF NOT EXISTS divergence (
  id INTEGER PRIMARY KEY,
  question_id TEXT NOT NULL,
  type TEXT NOT NULL,
  window_start INTEGER,
  window_end INTEGER,
  evidence_json TEXT,
  judge_json TEXT,
  rule_confidence TEXT
);
"""


# Columns added after the first local databases were created (M4, ADR 0007; T5.3: a database
# rebuilt from the committed snapshot has no texts, so it carries the uniformização flag).
_ADDED = {
    "classification": ("note TEXT", "text_source TEXT"),
    "acordao": ("uniformizacao INTEGER",),
}


def connect(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(DDL)
    for table, columns in _ADDED.items():
        have = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        for col in columns:
            if col.split()[0] not in have:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
    return conn
