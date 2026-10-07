# Enterprise RAG Knowledge Assistant

A retrieval-augmented generation system that answers cybersecurity questions
from a fixed set of public documents, with cited sources.

**Status:** work in progress (Day 3 of 10: ingestion, chunking, embedding complete).

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
- [ ] Generation with citations
- [ ] Evaluation
- [ ] Observability, Docker, CI, deployment

Run ingestion: data\processed\chunks.jsonl
Run order: python -m scripts.ingest,
           python -m scripts.init_db, 
           python -m scripts.load_chunks, 
           python -m scripts.search "your question"
My observations are here: docs/retrieval_notes.md