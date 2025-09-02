CREATE EXTENSION IF NOT EXISTS vector;
-- Example embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
  id BIGSERIAL PRIMARY KEY,
  doc_id TEXT,
  chunk_no INT,
  embedding vector(1536),
  meta JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);