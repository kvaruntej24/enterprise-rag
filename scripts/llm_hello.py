from app.generation.llm import generate

response = generate(
    system="You are a concise assistant.",
    user="In one sentence, what is retrieval-augmented generation?",
)
print(response.text)
print(
    f"tokens in/out: {response.input_tokens}/{response.output_tokens}, "
    f"latency: {response.latency_seconds:.2f}s"
)