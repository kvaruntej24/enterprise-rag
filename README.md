# Enterprise RAG Knowledge Assistant

A retrieval-augmented generation system that answers cybersecurity questions
from a fixed set of public documents, with cited sources.

**Status:** work in progress (Day 1 of 10: foundation complete).

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
- [x] Project foundation, database, corpus
- [ ] Ingestion and chunking
- [ ] Retrieval (semantic, BM25, hybrid, reranking)
- [ ] Generation with citations
- [ ] Evaluation
- [ ] Observability, Docker, CI, deployment