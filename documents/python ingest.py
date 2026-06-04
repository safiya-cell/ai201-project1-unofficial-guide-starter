"""
ingest.py — Milestone 3: Load, clean, and chunk RMP professor reviews
Domain   : Student reviews of CS professors at Lehman College
Strategy : Fixed-size character chunking (512 chars) with 50-char overlap
"""

import os
import re
import json

# ---------------------------------------------------------------------------
# 1. RAW DOCUMENTS
#    Paste scraped review text here (one string per professor).
#    Keys are professor IDs matching your planning.md sources.
# ---------------------------------------------------------------------------

RAW_DOCUMENTS = {
    "prof_3014815": """
        Professor was amazing! Very clear explanations and always willing to help
        during office hours. The exams were tough but fair. Highly recommend if
        you want to actually understand the material. Gave a lot of homework but
        it really prepared you for the tests. Would definitely take again.
    """,
    "prof_1847213": """
        Incredibly difficult class. The professor moves very fast and does not
        slow down for anyone. Office hours exist but they are not very helpful.
        Grading is harsh and the curve is minimal. Many students failed.
        Not recommended for beginners. Only take if you are strong in math.
    """,
    "prof_457502": """
        One of the best professors at Lehman. Very passionate about the subject
        and it shows. Makes even the most boring topics interesting. Always
        available via email and responds quickly. Assignments are reasonable and
        the rubric is always clear. Easy to follow lectures with good slides.
    """,
    "prof_2418146": """
        Average professor. Shows up, teaches from the slides, leaves. Not much
        engagement with students. The material is not explained in depth.
        Homework load is manageable. Tests are straight from the slides so easy
        to prepare if you study the deck. Would take again for an easy grade.
    """,
    "prof_3013308": """
        Tough grader but very knowledgeable. You will learn a lot if you put in
        the effort. Lectures can be dense and fast-paced. Participation matters.
        Group projects are a big portion of the grade. Professor gives useful
        feedback on assignments. Would recommend for motivated students only.
    """,
    "prof_2412165": """
        Very laid-back and easy-going professor. Never stressed about deadlines
        and gave extensions without complaint. The class content was light and
        the workload was low. Good professor for a chill semester. Some students
        felt the class was too easy and did not learn much. Depends on your goal.
    """,
    "prof_624955": """
        Explains concepts clearly and uses real-world examples. Homework is
        meaningful and directly ties to exams. Labs are well-structured. One of
        the more organized professors in the department. Highly interactive
        lectures. Students who attend every class do significantly better.
    """,
    "prof_487824": """
        Hard to follow during lectures. Speaks quickly and the board writing is
        unclear. Office hours are rarely held on time. Assignments are confusing
        with minimal instructions. Many students rely on YouTube to learn the
        actual material. Would not recommend unless you have no other option.
    """,
    "prof_1973094": """
        Great professor for introductory courses. Patient with beginners and
        explains everything step by step. Does not assume prior knowledge.
        Exams are straightforward if you attend class. Very approachable.
        Helpful during office hours and encourages questions in class.
    """,
    "prof_2668831": """
        Challenging but rewarding. The professor pushes you to think critically.
        Projects are complex but you learn a lot from them. Grading is strict
        but fair. Not ideal if you are looking for an easy A. Feedback on work
        is detailed and constructive. Would take again for upper-level courses.
    """,
}


# ---------------------------------------------------------------------------
# 2. CLEANING
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Remove noise from raw scraped review text:
    - Strip leading/trailing whitespace
    - Collapse multiple spaces and newlines into single spaces
    - Remove non-ASCII characters (e.g. smart quotes, emojis)
    - Normalize punctuation spacing
    """
    # Remove non-ASCII
    text = text.encode("ascii", errors="ignore").decode("ascii")

    # Collapse all whitespace (newlines, tabs, multiple spaces) into one space
    text = re.sub(r"\s+", " ", text)

    # Remove repeated punctuation (e.g. "!!!" → "!")
    text = re.sub(r"([!?.]){2,}", r"\1", text)

    # Strip
    text = text.strip()

    return text


# ---------------------------------------------------------------------------
# 3. CHUNKING
# ---------------------------------------------------------------------------

CHUNK_SIZE = 512   # characters
OVERLAP    = 50    # characters of overlap between consecutive chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """
    Split text into fixed-size character chunks with overlap.

    Args:
        text       : Cleaned input text.
        chunk_size : Maximum characters per chunk.
        overlap    : How many characters the next chunk re-uses from the end
                     of the previous chunk (prevents cutting mid-sentence context).

    Returns:
        List of chunk strings.
    """
    if not text:
        return []

    chunks = []
    start  = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        # Advance by (chunk_size - overlap) so the next chunk re-uses the
        # last `overlap` characters of the current chunk.
        start += chunk_size - overlap

        # Safety: if overlap >= chunk_size we'd loop forever
        if chunk_size <= overlap:
            raise ValueError("chunk_size must be greater than overlap")

    return chunks


# ---------------------------------------------------------------------------
# 4. PIPELINE
# ---------------------------------------------------------------------------

def run_pipeline(raw_docs: dict) -> list[dict]:
    """
    For each professor source:
      1. Clean the raw text
      2. Chunk it
      3. Return a list of records ready for embedding

    Each record contains:
      - source      : professor ID / URL key
      - chunk_index : position of this chunk within the source
      - text        : the chunk content
    """
    all_chunks = []

    for source_id, raw_text in raw_docs.items():
        cleaned = clean_text(raw_text)

        if not cleaned:
            print(f"[WARN] {source_id}: empty after cleaning, skipping.")
            continue

        chunks = chunk_text(cleaned)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "source":      source_id,
                "chunk_index": i,
                "text":        chunk,
            })

        print(f"[OK] {source_id}: {len(cleaned)} chars → {len(chunks)} chunk(s)")

    return all_chunks


# ---------------------------------------------------------------------------
# 5. MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Ingestion Pipeline — Lehman CS Professor Reviews")
    print(f"Chunk size : {CHUNK_SIZE} chars | Overlap : {OVERLAP} chars")
    print("=" * 60)

    chunks = run_pipeline(RAW_DOCUMENTS)

    # Save to JSONL for downstream embedding step (Milestone 4)
    output_path = "chunks.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for record in chunks:
            f.write(json.dumps(record) + "\n")

    print("=" * 60)
    print(f"Total chunks produced : {len(chunks)}")
    print(f"Saved to              : {output_path}")
    print("=" * 60)

    # Preview first 3 chunks
    print("\n--- Preview (first 3 chunks) ---\n")
    for record in chunks[:3]:
        print(f"Source      : {record['source']}")
        print(f"Chunk index : {record['chunk_index']}")
        print(f"Text        : {record['text'][:120]}...")
        print()
