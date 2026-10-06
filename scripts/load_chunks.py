import json
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from app.core.config import settings
from app.retrieval.embeddings import embed_texts

CHUNKS_PATH = Path("data/processed/chunks.jsonl")
BATCH_SIZE = 128
COLUMN_FIELDS = ("source", "doc_type", "page", "chunk_index")

UPSERT_SQL = """
INSERT INTO chunks
    (chunk_id, content, source, doc_type, page, chunk_index, metadata,
     embedding, embedding_model)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (chunk_id) DO UPDATE SET
    content = EXCLUDED.content,
    metadata = EXCLUDED.metadata,
    embedding = EXCLUDED.embedding,
    embedding_model = EXCLUDED.embedding_model
"""


def to_row(record: dict, vector) -> tuple:
    meta = record["metadata"]
    extra = {k: v for k, v in meta.items() if k not in COLUMN_FIELDS}
    return (
        record["chunk_id"],
        record["text"],
        meta["source"],
        meta["doc_type"],
        meta.get("page"),
        meta["chunk_index"],
        Jsonb(extra),
        vector,
        settings.embedding_model,
    )


def main() -> None:
    with CHUNKS_PATH.open(encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)

        existing = {
            row[0]
            for row in conn.execute(
                "SELECT chunk_id FROM chunks WHERE embedding_model = %s",
                (settings.embedding_model,),
            )
        }
        todo = [r for r in records if r["chunk_id"] not in existing]
        print(f"{len(records)} chunks in file, {len(existing)} already stored, "
              f"{len(todo)} to embed")

        for start in range(0, len(todo), BATCH_SIZE):
            batch = todo[start:start + BATCH_SIZE]
            vectors = embed_texts([r["text"] for r in batch])
            with conn.cursor() as cur:
                cur.executemany(UPSERT_SQL, [to_row(r, v) for r, v in zip(batch, vectors)])
            conn.commit()
            print(f"  stored {min(start + BATCH_SIZE, len(todo))}/{len(todo)}")

        keep_ids = [r["chunk_id"] for r in records]
        deleted = conn.execute(
            "DELETE FROM chunks WHERE chunk_id <> ALL(%s::text[])", (keep_ids,)
        ).rowcount
        conn.commit()
        print(f"removed {deleted} stale chunks")

        total = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
        print(f"table now has {total} chunks")


if __name__ == "__main__":
    main()