CREATE TABLE IF NOT EXISTS onsenstay (
  id TEXT PRIMARY KEY,
  agent_label TEXT,
  visit_reason TEXT NOT NULL,
  mood TEXT NOT NULL,
  current_activity TEXT NOT NULL,
  onsen_slug TEXT NOT NULL,
  variant_slug TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'active',
  turn_count INTEGER NOT NULL DEFAULT 0,
  meta_json JSON NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS stayturn (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stay_id TEXT NOT NULL,
  role TEXT NOT NULL,
  activity TEXT NOT NULL,
  content_json JSON NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_stayturn_stay_id ON stayturn(stay_id);
