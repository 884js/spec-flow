-- 0001_initial_schema.sql
-- spec-flow プラン管理 SQLite スキーマ

-- マイグレーションバージョン管理
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now'))
);

-- プロジェクト
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- プラン
CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    feature_name TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    body TEXT,
    mode TEXT DEFAULT 'single',
    current_situation TEXT,
    next_action TEXT,
    pr_groups TEXT,
    repositories TEXT,
    docs TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(project_id, feature_name)
);

-- タスク
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    task_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    UNIQUE(plan_id, task_number)
);

-- プラン間リレーション
CREATE TABLE IF NOT EXISTS plan_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    target_plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL DEFAULT 'related',
    description TEXT,
    UNIQUE(source_plan_id, target_plan_id)
);

-- 検証結果
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    judgment TEXT NOT NULL,
    body TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- リサーチ
CREATE TABLE IF NOT EXISTS research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES plans(id) ON DELETE SET NULL,
    topic TEXT NOT NULL,
    research_type TEXT,
    body TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- デバッグログ
CREATE TABLE IF NOT EXISTS debug_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES plans(id) ON DELETE SET NULL,
    body TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- コメント（Annotation Cycle 用）
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    section_heading TEXT,
    selected_text TEXT,
    comment TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- バージョン記録
INSERT OR IGNORE INTO schema_version (version) VALUES (1);
