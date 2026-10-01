OFFLINE: Documents → Parse → Chunk → Embed → Postgres (pgvector + metadata) + BM25 index

ONLINE:  Query → Semantic search ┐
                 BM25 search     ┴→ Fusion (RRF) → Rerank (cross-encoder)
         → Relevance gate (too low → "I don't know")
         → Context builder → LLM → Citation check → Answer + Sources

Cross-cutting: logging, tracing, latency/token/cost tracking, error handling
Quality loop: eval dataset → metrics → CI gate

# Architecture

## 1. What problem does this solve?
This system helps users get answers to cybersecurity questions from trusted sources like NIST documents. Instead of manually searching through many long PDFs, the system finds the relevant information and gives a direct answer. It also provides citations, so the user can check the original source. This makes the answers more reliable and easier to verify than using a general chatbot.

## 2. Why RAG instead of fine-tuning?
I chose RAG because cybersecurity information can change over time and the answers need to be traceable. With RAG, if a document or policy changes, I can simply update that document instead of retraining the whole model. RAG also allows me to show the exact source used for the answer and control which documents can be accessed. Fine-tuning is more useful for changing the model’s behavior, style, or format, so it could be used together with RAG later.

## 3. What happens during ingestion?
The ingestion process happens before the user asks any questions. First, we extract clean text from documents like PDFs, HTML, and Markdown and remove unnecessary content. Then, we split the text into smaller chunks so we can find specific information more accurately. Each chunk is converted into an embedding and stored in PostgreSQL with pgvector along with details like the source and page number. We also add the chunks to a BM25 keyword index, so later we can search using both meaning and exact keywords.

## 4. What happens when a user asks a question?
When the user asks a question, the system first converts the question into an embedding. Then it performs two searches at the same time: semantic search using pgvector and keyword search using BM25. The results from both searches are combined using Reciprocal Rank Fusion. A cross-encoder then reranks the results and selects the most relevant chunks.

Next, the system checks whether the results are relevant enough. If they are not, it responds that there is not enough information instead of asking the LLM to guess. If the results are relevant, we send the selected sources to the LLM and instruct it to answer only from those sources and include citations. Finally, we check that every citation actually points to a retrieved source before returning the answer.

## 5. Why semantic search and BM25?
I use both semantic search and keyword search because they have different strengths. Semantic search understands the meaning of a question, so it can find related information even when the exact words are different. For example, “stopping password guessing” can match a document about “account lockout.”

However, semantic search can sometimes confuse exact identifiers like control IDs or CVE numbers. BM25 is better for exact terms, but it may not understand synonyms or different ways of saying the same thing. So I use both searches and combine their results with Reciprocal Rank Fusion to get better and more reliable results.

## 6. What does the relevance gate do?
The relevance gate checks whether the best retrieved chunk is relevant enough to the user's question. It does not check whether the information is factually correct; it only checks whether the retrieved content is related to the question.

If the score is below the threshold, the system returns “I don't have enough information” and does not call the LLM. This saves cost, makes the response faster, and reduces the chance of the LLM generating an answer from irrelevant information.

The threshold is important. If it is too high, the system may reject useful information. If it is too low, irrelevant information may pass through. So I would choose and adjust the threshold using an evaluation dataset rather than guessing.

## 7. What happens when something fails?
I handle failures separately for each part of the system. If the database is unavailable, the API returns a simple 503 error to the user while the actual error is logged internally. A health-check endpoint also helps detect whether the service is working.

For LLM calls, I use timeouts and retry only temporary errors like timeouts, rate limits, or server errors. I use exponential backoff with a limited number of retries. Permanent errors, such as an invalid API key, fail immediately.

If the retries still fail, the system degrades gracefully, for example by returning the retrieved sources without generating an answer. If retrieval doesn't find relevant information, the relevance gate returns “I don't have enough information.”

Most importantly, the system fails closed, meaning it never generates an answer without relevant retrieved context. I also use request IDs and structured logs for debugging, while keeping technical errors and stack traces hidden from the user.

## Open questions

A. Why not send all the documents to the LLM in one prompt and skip retrieval?

I could send all the documents to the LLM, but that doesn't scale well. As the corpus grows, the prompt becomes larger, increasing token cost, latency, and the chance of distracting the model with irrelevant information. RAG retrieves only the most relevant chunks, so the LLM receives focused evidence for the question.
The core idea:- 10,000 documents → Retrieval → 5 relevant chunks → LLM
instead of:- 10,000 documents → LLM