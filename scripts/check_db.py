import numpy as np
import psycopg
from pgvector.psycopg import register_vector

from app.core.config import settings

with psycopg.connect(settings.database_url, autocommit=True) as conn:
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)

    conn.execute(
        "CREATE TEMP TABLE items "
        "(id serial PRIMARY KEY, label text, embedding vector(3))"
    )
    conn.execute(
        "INSERT INTO items (label, embedding) VALUES (%s, %s), (%s, %s), (%s, %s)",
        (
            "cat", np.array([1.0, 0.0, 0.0]),
            "dog", np.array([0.9, 0.1, 0.0]),
            "car", np.array([0.0, 0.0, 1.0]),
        ),
    )

    query = np.array([1.0, 0.05, 0.0])
    rows = conn.execute(
        "SELECT label, embedding <=> %s AS distance "
        "FROM items ORDER BY distance LIMIT 3",
        (query,),
    ).fetchall()

    for label, distance in rows:
        print(f"{label}: {distance:.4f}")