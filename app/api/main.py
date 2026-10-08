import logging
import time
import uuid
from contextlib import asynccontextmanager

import openai
import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.schemas import AskRequest, AskResponse, SourceOut
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.generation.pipeline import answer
from app.retrieval.bm25 import get_index
from app.retrieval.embeddings import get_model
from app.retrieval.rerank import get_reranker

setup_logging()
log = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup: loading models and building the BM25 index")
    get_model()
    get_reranker()
    get_index()
    log.info("startup complete")
    yield


app = FastAPI(title="Enterprise RAG Knowledge Assistant", lifespan=lifespan)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = uuid.uuid4().hex[:12]
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    log.info(
        "request_id=%s method=%s path=%s status=%d duration=%.2fs",
        request_id, request.method, request.url.path,
        response.status_code, time.perf_counter() - start,
    )
    return response


@app.get("/health")
def health():
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
    except Exception:
        log.exception("health check failed")
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, request: Request) -> AskResponse:
    request_id = request.state.request_id
    try:
        result = answer(body.question, k=body.k)
    except psycopg.Error:
        log.exception("request_id=%s database error", request_id)
        raise HTTPException(
            status_code=503,
            detail=f"The knowledge base is temporarily unavailable. Reference: {request_id}",
        )
    except openai.OpenAIError:
        log.exception("request_id=%s llm error", request_id)
        raise HTTPException(
            status_code=502,
            detail=f"The language model service is unavailable. Reference: {request_id}",
        )
    except Exception:
        log.exception("request_id=%s unexpected error", request_id)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error. Reference: {request_id}",
        )

    warnings: list[str] = []
    if result.invalid_citations:
        warnings.append(f"Answer cites sources that were not provided: {result.invalid_citations}")
    if result.uncited:
        warnings.append("Answer has no valid citations")

    log.info(
        "request_id=%s refused=%s reason=%s top_score=%.2f question_chars=%d "
        "retrieval=%.2fs llm=%.2fs tokens=%d/%d warnings=%d",
        request_id, result.refused, result.refusal_reason or "-", result.top_score,
        len(body.question), result.retrieval_seconds, result.llm_seconds,
        result.input_tokens, result.output_tokens, len(warnings),
    )

    return AskResponse(
        request_id=request_id,
        answer=result.text,
        refused=result.refused,
        refusal_reason=result.refusal_reason,
        sources=[
            SourceOut(number=n, source=c.source, page=c.page,
                      doc_type=c.doc_type, snippet=c.content[:200])
            for n, c in sorted(result.cited.items())
        ],
        warnings=warnings,
        retrieval_seconds=result.retrieval_seconds,
        llm_seconds=result.llm_seconds,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )