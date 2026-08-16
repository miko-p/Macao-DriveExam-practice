-- 题库 + 练习进度 schema（SQLite）
-- 由 database/store.py 在初始化时执行

CREATE TABLE IF NOT EXISTS questions (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id    TEXT UNIQUE,            -- 网站原题 id（去重用；若页面无稳定id则为哈希）
  subject      TEXT,                   -- 章节/类别（A组、机械常识…）
  stem         TEXT NOT NULL,          -- 题干
  choices      TEXT NOT NULL,          -- JSON ["A...","B...","C...","D..."]
  answer       TEXT NOT NULL,          -- 正确选项字母，如 "B"
  explanation  TEXT,                   -- 解析（若页面有）
  created_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS practice_log (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  qid         INTEGER NOT NULL REFERENCES questions(id),
  correct     INTEGER NOT NULL,        -- 1 对 / 0 错
  mode        TEXT,                    -- 顺序/随机/章节/错题/模拟考
  answered_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject);
CREATE INDEX IF NOT EXISTS idx_practice_qid ON practice_log(qid);
