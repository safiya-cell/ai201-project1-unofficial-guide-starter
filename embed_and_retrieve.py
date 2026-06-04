"""
embed_and_retrieve.py — Milestone 4: Embedding and Retrieval
Domain   : Student reviews of CS professors at Lehman College
Model    : sentence-transformers/all-MiniLM-L6-v2
Store    : ChromaDB (local persistent)
Pipeline : chunks.jsonl → embed → ChromaDB → retrieve(query, top_k)

Architecture:
  [chunks.jsonl]
       │
       ▼
  load_chunks()
       │
       ▼
  embed_chunks()  ←  all-MiniLM-L6-v2
       │
       ▼
  ChromaDB collection  (text + embeddings + metadata)
       │
       ▼
  retrieve(query, top_k)  →  ranked results
"""

import json
import os
from pathlib import Path

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

CHUNKS_FILE     = "chunks.jsonl"        # output from ingest.py
CHROMA_DIR      = "chroma_store"        # local folder ChromaDB writes to
COLLECTION_NAME = "professor_reviews"
EMBED_MODEL     = "all-MiniLM-L6-v2"
TOP_K_DEFAULT   = 5


# ---------------------------------------------------------------------------
# 1. LOAD CHUNKS
# ---------------------------------------------------------------------------

def load_chunks(path: str = CHUNKS_FILE) -> list[dict]:
    """
    Load chunks produced by ingest.py from a JSONL file.
    Each line is: {"source": ..., "review_index": ..., "chunk_index": ..., "text": ...}
    """
    if not Path(path).exists():
        raise FileNotFoundError(
            f"'{path}' not found. Run ingest.py first to generate chunks."
        )

    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                # Skip empty text chunks defensively
                if record.get("text", "").strip():
                    chunks.append(record)
                else:
                    print(f"[WARN] Line {line_num}: empty text, skipping.")
            except json.JSONDecodeError as e:
                print(f"[WARN] Line {line_num}: JSON parse error — {e}")

    print(f"[load_chunks] Loaded {len(chunks)} chunks from '{path}'")
    return chunks


# ---------------------------------------------------------------------------
# 2. BUILD CHROMA CLIENT + COLLECTION
# ---------------------------------------------------------------------------

def get_collection(persist_dir: str = CHROMA_DIR):
    """
    Create (or open existing) a persistent ChromaDB collection.
    ChromaDB stores embeddings + metadata locally in `persist_dir`.
    """
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine similarity for semantic search
    )
    return collection


# ---------------------------------------------------------------------------
# 3. EMBED AND STORE
# ---------------------------------------------------------------------------

def embed_and_store(
    chunks: list[dict],
    collection,
    model_name: str = EMBED_MODEL,
    batch_size: int = 64,
) -> None:
    """
    Embed each chunk with all-MiniLM-L6-v2 and upsert into ChromaDB.

    ChromaDB document structure per chunk:
      - id        : unique string ID  (source + review_index + chunk_index)
      - embedding : 384-dim float vector from all-MiniLM-L6-v2
      - document  : raw chunk text (stored for display in results)
      - metadata  : source professor ID, review_index, chunk_index
    """
    # Check if collection already populated — skip re-embedding if so
    existing_count = collection.count()
    if existing_count > 0:
        print(f"[embed_and_store] Collection already has {existing_count} entries.")
        print("  Skipping re-embedding. Delete 'chroma_store/' to re-index.")
        return

    print(f"[embed_and_store] Loading model: {model_name}")
    model = SentenceTransformer(model_name)

    texts     = [c["text"] for c in chunks]
    ids       = [
        f"{c['source']}_r{c['review_index']}_c{c['chunk_index']}"
        for c in chunks
    ]
    metadatas = [
        {
            "source":       c["source"],
            "review_index": c["review_index"],
            "chunk_index":  c["chunk_index"],
        }
        for c in chunks
    ]

    print(f"[embed_and_store] Embedding {len(texts)} chunks in batches of {batch_size}...")

    # Embed in batches to avoid memory issues on large corpora
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        embeddings = model.encode(batch, show_progress_bar=False).tolist()
        all_embeddings.extend(embeddings)
        print(f"  Embedded {min(i + batch_size, len(texts))} / {len(texts)}")

    # Upsert into ChromaDB (insert or update if ID already exists)
    collection.upsert(
        ids        = ids,
        embeddings = all_embeddings,
        documents  = texts,
        metadatas  = metadatas,
    )

    print(f"[embed_and_store] Stored {len(texts)} chunks in ChromaDB at '{CHROMA_DIR}/'")


# ---------------------------------------------------------------------------
# 4. RETRIEVAL
# ---------------------------------------------------------------------------

def retrieve(
    query: str,
    collection,
    model_name: str = EMBED_MODEL,
    top_k: int = TOP_K_DEFAULT,
) -> list[dict]:
    """
    Embed the query and find the top_k most similar chunks in ChromaDB.

    Returns a list of dicts, each with:
      - rank         : 1-based position
      - source       : professor ID
      - review_index : which review it came from
      - chunk_index  : which chunk within that review
      - text         : the chunk text
      - score        : cosine distance (lower = more similar; 0 = identical)
    """
    model = SentenceTransformer(model_name)
    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings = query_embedding,
        n_results        = top_k,
        include          = ["documents", "metadatas", "distances"],
    )

    # Unpack ChromaDB response structure
    retrieved = []
    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]

    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
        retrieved.append({
            "rank":         rank,
            "source":       meta["source"],
            "review_index": meta["review_index"],
            "chunk_index":  meta["chunk_index"],
            "text":         doc,
            "score":        round(dist, 4),   # cosine distance (0 = best match)
        })

    return retrieved


# ---------------------------------------------------------------------------
# 5. PRETTY PRINT RESULTS
# ---------------------------------------------------------------------------

def print_results(query: str, results: list[dict]) -> None:
    print(f"\n{'='*60}")
    print(f"Query : {query}")
    print(f"{'='*60}")
    if not results:
        print("No results returned.")
        return
    for r in results:
        print(f"\n  Rank {r['rank']}  |  {r['source']}  |  score: {r['score']}")
        print(f"  {r['text']}")
    print()


# ---------------------------------------------------------------------------
# 6. MAIN — full pipeline + sample queries
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # Step 1: Load chunks from ingest.py output
    chunks = load_chunks(CHUNKS_FILE)

    # Step 2: Connect to (or create) ChromaDB collection
    collection = get_collection(CHROMA_DIR)

    # Step 3: Embed and store (skips automatically if already indexed)
    embed_and_store(chunks, collection)

    print(f"\n[ready] Collection contains {collection.count()} chunks.\n")

    # Step 4: Run your 5 evaluation queries from planning.md
    eval_queries = [
        "What do students say about the professors' teaching at the college?",
        "What are students saying about the teachers' personalities?",
        "What makes students want to take certain professors again?",
        "What prevents students from taking certain professors again?",
        "What do students say about the assignments given?",
    ]

    for query in eval_queries:
        results = retrieve(query, collection, top_k=TOP_K_DEFAULT)
        print_results(query, results)
