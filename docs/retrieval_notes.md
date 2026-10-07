# Retrieval notes (semantic search only)

Setup: BAAI/bge-small-en-v1.5, 1000-char chunks, cosine similarity, top 3 shown.
Note: file-level expectations were filled in after the first run, so treat
them as less rigorous than a pre-registered evaluation set (Day 7).

| Query | Expected source | In top 3? | Top score | Notes |
-------------------------------------------------------------------------------
| How should passwords be stored? | Password_Storage_Cheat_Sheet.md | yes | 0.831 | #2 Cryptographic Storage also relevant |
| What should I log for security events? | Logging_Cheat_Sheet.md | yes | 0.781 | #2 is a CISA ransomware chunk at 0.779 |
| How do I stop an attacker from injecting SQL commands? | A03 Injection (OWASP) | yes | 0.762 | all 3 results from one file |
| What are the main phases of incident response? | NIST.SP.800-61r3.pdf | yes | 0.802 | right document |
| What does zero trust mean? | NIST.SP.800-207.pdf | yes | 0.824 |
| How do I prevent insecure deserialization? | Deserialization_Cheat_Sheet.md | yes | 0.834 |
| What should an organization do first when hit by ransomware? | NCSC/CISA | yes | 0.808 |
| GV.OC-03 | page from SQL check | not really | 0.665 | low scores, P.18 contains the string but was not in the top 3 |
| FIPS 199 high impact | NIST.FIPS.199.pdf | yes | 0.618 | #3 unrelated (OWASP LLM), correct hit has a low score |
| PW.4 | NIST.SP.800-218.pdf | yes | 0.687 |  SQL result |
| LLM01 prompt injection | OWASP-Top-10-for-LLMs | likely | 0.771 | words "prompt injection" help; not a pure ID test |
| Table 1 vulnerability mitigation time summary matrix | NIST.SP.800-40r4.pdf p.24 | yes | 0.759 | 3 chunks from p.24: table probably split |
| What is the best pizza topping? | none | n/a | 0.516 | well below real hits |
| How do I configure Kubernetes network policies? | none expected | n/a | 0.662 | higher than the correct FIPS 199 hit (0.618) |

## Conclusions

Semantic search handled natural-language questions well: for all seven, the top result came from the file i expected. 
It was weaker on exact identifiers(GV.OC-03, PW.4), where scores were lower and the chunk containing the literal string was not guaranteed to rank first.
Raw similarity scores also cannot separate answerable from unanswerable questions: an out-of-corpus question (0.662) scored higher than a correct hit (0.618). This motivates BM25 for exact terms, a reranker for finer ordering, and a threshold calibrated on labeled questions. 
Table 1 appears split across chunks, which is a chunking limitation to evaluate.