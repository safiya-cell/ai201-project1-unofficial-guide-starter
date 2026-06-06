"""
app.py — Milestone 5: Generation and Gradio Interface
Domain : Student reviews of CS professors at Lehman College

Pipeline:
  User query
      │
      ▼
  retrieve()          ← embed_and_retrieve.py  (ChromaDB + all-MiniLM-L6-v2)
      │
      ▼
  build_prompt()      ← grounded: only retrieved chunks passed to LLM
      │
      ▼
  generate()          ← Groq (llama3-8b-8192)
      │
      ▼
  Gradio UI           ← answer + source attribution list
"""

import os
from dotenv import load_dotenv
from groq import Groq
import gradio as gr

# Import retrieval components from Milestone 4
from embed_and_retrieve import load_chunks, get_collection, embed_and_store, retrieve

load_dotenv()

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

GROQ_MODEL      = "llama3-8b-8192"
TOP_K           = 5
MAX_SCORE       = 0.65      # drop chunks weaker than this threshold
CHUNKS_FILE     = "chunks.jsonl"
CHROMA_DIR      = "chroma_store"

# ---------------------------------------------------------------------------
# INIT — load once at startup
# ---------------------------------------------------------------------------

print("[startup] Loading chunks and embedding store...")
_chunks     = load_chunks(CHUNKS_FILE)
_collection = get_collection(CHROMA_DIR)
embed_and_store(_chunks, _collection)   # no-op if already indexed
_groq       = Groq(api_key=os.getenv("GROQ_API_KEY"))
print(f"[startup] Ready. Collection has {_collection.count()} chunks.")


# ---------------------------------------------------------------------------
# 1. PROMPT BUILDER
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an unofficial guide to CS professors at Lehman College.
You answer student questions ONLY using the review excerpts provided below.
Rules:
- Base every claim on the provided excerpts. Do not add outside knowledge.
- If the excerpts do not contain enough information to answer, say so clearly.
- Be helpful, direct, and neutral in tone.
- Do not invent professor names, ratings, or opinions not present in the excerpts."""


def build_prompt(query: str, retrieved: list[dict]) -> str:
    """
    Construct a grounded prompt by injecting retrieved chunks as context.
    Each chunk is labelled with its source so the model can attribute claims.
    """
    if not retrieved:
        return f"Question: {query}\n\nNo relevant reviews were found."

    context_lines = []
    for r in retrieved:
        context_lines.append(
            f"[Source: {r['source']} | review {r['review_index']}]\n{r['text']}"
        )
    context_block = "\n\n".join(context_lines)

    return (
        f"Use ONLY the following student review excerpts to answer the question.\n\n"
        f"--- EXCERPTS ---\n{context_block}\n--- END EXCERPTS ---\n\n"
        f"Question: {query}\n\n"
        f"Answer (cite sources by their [Source: ...] label where relevant):"
    )


# ---------------------------------------------------------------------------
# 2. GENERATION
# ---------------------------------------------------------------------------

def generate(query: str, retrieved: list[dict]) -> str:
    """
    Call Groq with the grounded prompt and return the model's answer.
    """
    if not retrieved:
        return "No relevant reviews were found for your query. Try rephrasing or asking about a different aspect of professors at Lehman."

    prompt = build_prompt(query, retrieved)

    response = _groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.2,    # low temp = factual, grounded answers
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# 3. SOURCE FORMATTER
# ---------------------------------------------------------------------------

def format_sources(retrieved: list[dict]) -> str:
    """
    Build a readable source attribution list shown below the answer.
    Format: Rank · professor ID · cosine score · chunk preview
    """
    if not retrieved:
        return "_No sources retrieved._"

    lines = ["**Sources used:**\n"]
    for r in retrieved:
        preview = r["text"][:120].replace("\n", " ")
        if len(r["text"]) > 120:
            preview += "..."
        lines.append(
            f"**{r['rank']}.** `{r['source']}` "
            f"(review {r['review_index']}, score: {r['score']})\n"
            f"> {preview}\n"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. FULL PIPELINE FUNCTION (called by Gradio)
# ---------------------------------------------------------------------------

def answer_query(query: str):
    """
    End-to-end: query → retrieve → generate → return (answer, sources).
    This is the function Gradio calls on submit.
    """
    query = query.strip()
    if not query:
        return "Please enter a question.", ""

    # Retrieve relevant chunks
    retrieved = retrieve(
        query      = query,
        collection = _collection,
        top_k      = TOP_K,
        # Filter weak matches before passing to generator
    )

    # Drop chunks that are too weakly matched
    retrieved = [r for r in retrieved if r["score"] <= MAX_SCORE]

    # Generate grounded answer
    answer  = generate(query, retrieved)
    sources = format_sources(retrieved)

    return answer, sources


# ---------------------------------------------------------------------------
# 5. GRADIO INTERFACE
# ---------------------------------------------------------------------------

EXAMPLE_QUERIES = [
    "What do students say about the professors' teaching style?",
    "Which professors are known for being approachable and helpful?",
    "What makes students want to take certain professors again?",
    "Which professors give a lot of homework and projects?",
    "What prevents students from taking certain professors again?",
]

with gr.Blocks(
    title="Lehman CS Professor Guide",
    theme=gr.themes.Soft(
        primary_hue="slate",
        secondary_hue="blue",
    ),
) as demo:

    # Header
    gr.Markdown(
        """
        # 📚 Lehman CS Professor Guide
        _Ask anything about CS professors at Lehman College — answers grounded in real student reviews._
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            query_box = gr.Textbox(
                label="Your question",
                placeholder="e.g. Which professor explains concepts most clearly?",
                lines=2,
            )
            submit_btn = gr.Button("Ask", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("**Example questions:**")
            for ex in EXAMPLE_QUERIES:
                gr.Button(ex, size="sm").click(
                    fn=lambda q=ex: q,
                    outputs=query_box,
                )

    gr.Markdown("---")

    with gr.Row():
        with gr.Column(scale=2):
            answer_box = gr.Markdown(label="Answer", value="_Your answer will appear here._")

        with gr.Column(scale=1):
            sources_box = gr.Markdown(label="Sources", value="_Retrieved sources will appear here._")

    # Wire submit button
    submit_btn.click(
        fn     = answer_query,
        inputs = [query_box],
        outputs= [answer_box, sources_box],
    )

    # Also allow Enter key to submit
    query_box.submit(
        fn     = answer_query,
        inputs = [query_box],
        outputs= [answer_box, sources_box],
    )

    gr.Markdown(
        """
        ---
        <small>Answers are grounded in retrieved student reviews only.
        Sources shown with cosine similarity scores — lower score = stronger match.</small>
        """
    )

# ---------------------------------------------------------------------------
# 6. MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo.launch(
        server_name = "0.0.0.0",
        server_port = 7860,
        share       = False,    # set True to get a public Gradio link
    )
