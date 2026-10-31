- v1.1: removed duplicate u101; 
- removed u108 , u111, q027(corpus mentions...); 
- rewrote q026,q025 (not self-contained);
- every call was failing becoz of the rate limit , i then changed the workflow into
Re-judge only the failed questions.
## Day 9: judge reliability
- The regression gate failed on faithfulness (0.92 -> 0.80). Diagnosis: 7 of 25 judge calls returned no verdict (6 daily token-limit errors, 1 empty reply), and the metric counted them as unfaithful.
- Re-judging identical baseline answers gave the same verdict on 24 of 25 questions (the 25th was a judge error), so the judge is stable when it answers but fails intermittently.
- Fixes: judge retries with backoff, larger max_tokens, errors excluded from rates and reported as judge_error_rate (also gated), and a retry-only-errors option.
- After the fix: 0 of 25 judge errors; faithful 22/25 (0.88) vs baseline 23/25 (0.92); the gate passes at tolerance 0.10. The difference is one question (q016, answer wording changed between runs).
- Tolerance was not changed. Failed attempt kept as judge_current_run1.json.
- Questions 27 and 34 were removed coz they are directly refering to exact terminology in corpus, that results in clean retrival and generation but doesn't messure model performance.