import sys
import time

from app.retrieval.retriever import retrieve

sys.stdout.reconfigure(encoding="utf-8")

QUESTIONS = [
    ("answerable", "How should passwords be stored?"),
    ("answerable", "What should I log for security events?"),
    ("answerable", "How do I stop an attacker from injecting SQL commands?"),
    ("answerable", "What are the main phases of incident response?"),
    ("answerable", "What does zero trust mean?"),
    ("answerable", "How do I prevent insecure deserialization?"),
    ("answerable", "What should an organization do first when hit by ransomware?"),
    ("answerable", "What does GV.OC-03 refer to?"),
    ("answerable", "What does PW.4 refer to?"),
    ("answerable", "What is FIPS 199 high impact?"),
    ("answerable", "In the NIST patching guide, what percent of critical "
                   "vulnerabilities on high-importance assets were patched by the deadline?"),
    ("not in corpus", "What is the best pizza topping?"),
    ("not in corpus", "How do I configure Kubernetes network policies?"),
    ("not in corpus", "Who won the 2022 football World Cup?"),
    ("not in corpus", "How do I configure AWS IAM roles?"),
]

retrieve("warm up the models", k=1)
total = 0.0
for kind, question in QUESTIONS:
    start = time.perf_counter()
    top = retrieve(question, k=3)[0]
    total += time.perf_counter() - start
    page = f" p.{top.page}" if top.page else ""
    print(f"{kind:14} {top.score:7.2f}  {top.source}{page}  | {question[:55]}")
print(f"\naverage retrieval time (after warm-up): {total / len(QUESTIONS):.2f}s")