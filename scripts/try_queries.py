from app.retrieval.semantic import semantic_search

QUERIES = [
    # meaning-based questions
    "How should passwords be stored?",
    "What should I log for security events?",
    "How do I stop an attacker from injecting SQL commands?",
    "What are the main phases of incident response?",
    "What does zero trust mean?",
    "How do I prevent insecure deserialization?",
    "What should an organization do first when hit by ransomware?",
    # exact-term questions
    "GV.OC-03",
    "FIPS 199 high impact",
    "PW.4",
    "LLM01 prompt injection",
    "Table 1 vulnerability mitigation time summary matrix",
    # questions the corpus should NOT answer
    "What is the best pizza topping?",
    "How do I configure Kubernetes network policies?",
]

for q in QUERIES:
    print(f"\nQ: {q}")
    for r in semantic_search(q, k=3):
        page = f" p.{r.page}" if r.page else ""
        print(f"   [{r.score:.3f}] {r.source}{page}")