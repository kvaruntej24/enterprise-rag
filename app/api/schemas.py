from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    k: int = Field(default=5, ge=1, le=10)


class SourceOut(BaseModel):
    number: int
    source: str
    page: int | None
    doc_type: str
    snippet: str


class AskResponse(BaseModel):
    request_id: str
    answer: str
    refused: bool
    refusal_reason: str
    sources: list[SourceOut]
    warnings: list[str]
    retrieval_seconds: float
    llm_seconds: float
    input_tokens: int
    output_tokens: int