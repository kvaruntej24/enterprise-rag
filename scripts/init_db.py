import psycopg

from app.core.config import settings

STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    f"""
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id        text PRIMARY KEY,
        content         text NOT NULL,
        source          text NOT NULL,
        doc_type        text NOT NULL,
        page            integer,
        chunk_index     integer NOT NULL,
        metadata        jsonb NOT NULL DEFAULT '{{}}',
        embedding       vector({settings.embedding_dim}) NOT NULL,
        embedding_model text NOT NULL,
        created_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops)
    """,
    "CREATE INDEX IF NOT EXISTS chunks_source_idx ON chunks (source)",
]


def main() -> None:
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        for statement in STATEMENTS:
            conn.execute(statement)

        print("Columns:")
        for name, dtype in conn.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'chunks' ORDER BY ordinal_position"
        ):
            print(f"  {name}: {dtype}")

        print("Indexes:")
        for (name,) in conn.execute(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'chunks'"
        ):
            print(f"  {name}")


if __name__ == "__main__":
    main()