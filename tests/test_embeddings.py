import numpy as np

from app.retrieval.embeddings import embed_query, embed_texts


def test_embeddings_have_expected_shape_and_are_normalized():
    vectors = embed_texts(["hello world", "another sentence"])
    assert vectors.shape == (2, 384)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-3)


def test_related_text_scores_higher_than_unrelated():
    query = embed_query("How should passwords be stored?")
    related, unrelated = embed_texts([
        "Passwords must be hashed with a slow algorithm such as Argon2.",
        "The football match ended in a draw after extra time.",
    ])
    assert query @ related > query @ unrelated