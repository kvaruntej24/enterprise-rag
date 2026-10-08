# Enterprise RAG Knowledge Assistant

A retrieval-augmented generation system that answers cybersecurity questions
from a fixed set of public documents, with cited sources.

**Status:** work in progress (Day 5 of 10: relevance gate, FastAPI, logging, and error handling. complete).

## Architecture
See [docs/architecture.md](docs/architecture.md).

## Setup (Windows)

1. Clone the repo and enter the folder.

   git clone https://github.com/kvaruntej24/enterprise-rag.git
   cd enterprise-rag

2. Create and activate a virtual environment:

       python -m venv .venv
       .venv\Scripts\activate

3. Install dependencies:

       pip install -r requirements.txt

4. Copy the environment template:

       copy .env.example.env

5. Start the database (requires Docker Desktop):

       docker compose up -d

6. Verify the database connection:

       python -m scripts.check_db

## Data
The documents are not stored in this repository. See
[data/SOURCES.md](data/SOURCES.md) for sources and licenses.

## Roadmap
- [X] Project foundation, database, corpus
- [X] Retrieval (semantic, BM25, hybrid, reranking)
- [X] Generation with citations
- [ ] Evaluation
- [ ] Observability, Docker, CI, deployment

Run ingestion: data\processed\chunks.jsonl
Run order: python -m scripts.ingest,
           python -m scripts.init_db, 
           python -m scripts.load_chunks, 
           python -m scripts.search "your question"

Run the API: python -m uvicorn app.api.main:app --port 8000, then open /docs.

My observations are here: docs/retrieval_notes.md
no relevance gate yet (out-of-corpus questions still send irrelevant chunks to the LLM); the model sometimes drifts from the citation format (we normalize it);
a table question was falsely refused; 
there's no evaluation set yet.
models load at startup; the endpoint is def because the pipeline blocks; request IDs and logs; the question text isn't logged.


Known limitations: 
the gate threshold of 1.0 is provisional, based on a 15-question probe; 
the table question is still refused; 
there's no evaluation set yet; 
and the API runs as a single process.