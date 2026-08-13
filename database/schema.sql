CREATE TABLE IF NOT EXISTS movie_analysis (
    id_title    TEXT PRIMARY KEY,
    result_data TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS background_tasks (
    task_id TEXT PRIMARY KEY,
    task_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
