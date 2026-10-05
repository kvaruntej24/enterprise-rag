import json
import time

from app.retrieval.embeddings import embed_query, embed_texts, get_model

model = get_model()
print(f"model: max {model.max_seq_length} tokens, "
      f"{model.get_sentence_embedding_dimension()} dimensions")

with open("data/processed/chunks.jsonl", encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]
texts = [c["text"] for c in chunks[::8]]

token_counts = [len(model.tokenizer.encode(t)) for t in texts]
too_long = sum(1 for n in token_counts if n > model.max_seq_length)
print(f"tokens per chunk: avg {sum(token_counts) // len(token_counts)}, "
      f"max {max(token_counts)}, over the limit: {too_long}")

start = time.perf_counter()
vectors = embed_texts(texts)
elapsed = time.perf_counter() - start
print(f"embedded {len(texts)} chunks in {elapsed:.1f}s -> shape {vectors.shape}")
print(f"estimated time for all {len(chunks)} chunks: "
      f"{elapsed * len(chunks) / len(texts):.0f}s")

print("query vector shape:", embed_query("How should passwords be stored?").shape)