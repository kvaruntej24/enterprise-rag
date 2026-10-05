from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
print("Embedding dimension:", model.get_sentence_embedding_dimension())

sentences = [
    "How do I stop someone from guessing passwords?",
    "Account lockout and brute-force protection limit repeated login attempts.",
    "Backups should be stored offline to survive ransomware attacks.",
]

embeddings = model.encode(sentences, normalize_embeddings=True)
print("Shape:", embeddings.shape)

scores = embeddings @ embeddings.T
for i, sentence in enumerate(sentences):
    print(i, sentence)
print(scores.round(3))