"""
ingest.py — Milestone 3: Load, clean, and chunk RMP professor reviews
Fixes:
  - Filters empty chunks
  - Cleans HTML tags and entities
  - Chunks per individual review (better boundary respect)
  - Prints raw vs cleaned comparison for debugging
"""

import re
import json
from html import unescape

# ---------------------------------------------------------------------------
# 1. RAW DOCUMENTS
#    Structure: each professor has a LIST of individual reviews.
#    This naturally respects content boundaries — one review = one unit.
# ---------------------------------------------------------------------------

RAW_DOCUMENTS = {
    "prof_3014815": [
        "Professor was amazing! Very clear explanations and always willing to help during office hours. The exams were tough but fair. Highly recommend if you want to actually understand the material. Gave a lot of homework but it really prepared you for the tests. Would definitely take again.",
        "Best professor I&#39;ve had at Lehman. <span class='highlight'>Very organized</span> and posts slides before class. Grading is transparent. Always replies to emails within 24 hours. The workload is heavy but manageable if you stay on top of it.",
        "Difficult but worth it. You will not pass by just showing up. Active participation and doing every assignment is the only way to do well. Professor is strict but genuinely wants students to succeed. Office hours are very productive.",
    ],
    "prof_1847213": [
        "Incredibly difficult class. The professor moves very fast and does not slow down for anyone. Office hours exist but they are not very helpful. Grading is harsh and the curve is minimal. Many students failed. Not recommended for beginners.",
        "Avoid if you can. Lectures are hard to follow and the professor gets frustrated when asked basic questions. Assignments are vague. Would not recommend for anyone who does not already know the subject well.",
        "Not the worst but not great either. You learn the material eventually but it takes a lot of outside studying. The textbook helps more than the lectures honestly. Exams are fair if you read every chapter.",
    ],
    "prof_457502": [
        "One of the best professors at Lehman. Very passionate about the subject and it shows. Makes even the most boring topics interesting. Always available via email and responds quickly.",
        "Loved this class. Professor explains everything step by step and never makes you feel dumb for asking questions. Assignments are reasonable and the rubric is always clear. Would take every class they teach.",
        "Great teacher. The lectures are engaging and the examples used are very relevant. Homework is graded fairly. Exams are tough but directly based on what was taught in class. 10 out of 10 would recommend.",
    ],
    "prof_2418146": [
        "Average professor. Shows up, teaches from the slides, leaves. Not much engagement with students. Tests are straight from the slides so easy to prepare if you study the deck.",
        "Not inspiring but not harmful either. Gets the job done. If you want a professor who will push you, look elsewhere. If you need an easy pass, this works.",
    ],
    "prof_3013308": [
        "Tough grader but very knowledgeable. You will learn a lot if you put in the effort. Lectures can be dense and fast-paced. Participation matters a lot in the final grade.",
        "Group projects are a big portion of the grade. Professor gives useful feedback on assignments. Would recommend for motivated students only. Not suitable if you want a relaxed semester.",
    ],
    "prof_2412165": [
        "Very laid-back and easy-going professor. Never stressed about deadlines and gave extensions without complaint. The class content was light and the workload was low.",
        "Good professor for a chill semester. Some students felt the class was too easy and did not learn much. Depends on your goal. If you need an easy elective this is the one.",
    ],
    "prof_624955": [
        "Explains concepts clearly and uses real-world examples. Homework is meaningful and directly ties to exams. Labs are well structured and organized.",
        "One of the more organized professors in the department. Highly interactive lectures. Students who attend every class do significantly better on exams.",
    ],
    "prof_487824": [
        "Hard to follow during lectures. Speaks quickly and the board writing is unclear. Office hours are rarely held on time. Would not recommend unless you have no other option.",
        "Assignments are confusing with minimal instructions. Many students rely on YouTube to learn the actual material. Feedback on work is nearly nonexistent.",
    ],
    "prof_1973094": [
        "Great professor for introductory courses. Patient with beginners and explains everything step by step. Does not assume prior knowledge.",
        "Very approachable. Helpful during office hours and encourages questions in class. Exams are straightforward if you attend every lecture.",
    ],
    "prof_2668831": [
        "Challenging but rewarding. The professor pushes you to think critically. Projects are complex but you learn a lot from them. Grading is strict but fair.",
        "Feedback on work is detailed and constructive. Would take again for upper-level courses. Not ideal if you are looking for an easy A.",
    ],
}


# ---------------------------------------------------------------------------
# 2. CLEANING
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    # Decode HTML entities first (e.g. &#39; → ' and &amp; → &)
    text = unescape(text)

    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove non-ASCII characters
    text = text.encode("ascii", errors="ignore").decode("ascii")

    # Collapse all whitespace into a single space
    text = re.sub(r"\s+", " ", text)

    # Remove repeated punctuation
    text = re.sub(r"([!?.]){2,}", r"\1", text)

    return text.strip()


# ---------------------------------------------------------------------------
# 3. CHUNKING (per-review with fixed-size fallback)
# ---------------------------------------------------------------------------

CHUNK_SIZE = 512
OVERLAP    = 50


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list:
    """
    Split a single review into chunks if it exceeds chunk_size.
    Filters out empty or whitespace-only chunks.
    """
    if not text:
        return []

    # If the review fits in one chunk, return it directly
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start  = 0
    step   = chunk_size - overlap

    if step <= 0:
        raise ValueError("chunk_size must be greater than overlap")

    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if len(chunk) > 0:          # ← empty chunk filter
            chunks.append(chunk)
        start += step

    return chunks


# ---------------------------------------------------------------------------
# 4. PIPELINE
# ---------------------------------------------------------------------------

def run_pipeline(raw_docs: dict, debug: bool = False) -> list:
    all_chunks = []

    for source_id, reviews in raw_docs.items():
        source_chunks = []

        for review_index, raw_text in enumerate(reviews):

            # Debug: show raw vs cleaned for first review of first professor
            if debug and review_index == 0 and len(all_chunks) == 0:
                print("\n--- DEBUG: Raw vs Cleaned (first review) ---")
                print(f"RAW     : {raw_text[:120]}")
                cleaned_preview = clean_text(raw_text)
                print(f"CLEANED : {cleaned_preview[:120]}")
                print()

            cleaned = clean_text(raw_text)

            if not cleaned:
                print(f"[WARN] {source_id} review {review_index}: empty after cleaning")
                continue

            chunks = chunk_text(cleaned)

            for chunk_i, chunk in enumerate(chunks):
                source_chunks.append({
                    "source":       source_id,
                    "review_index": review_index,
                    "chunk_index":  chunk_i,
                    "text":         chunk,
                })

        print(f"[OK] {source_id}: {len(reviews)} review(s) → {len(source_chunks)} chunk(s)")
        all_chunks.extend(source_chunks)

    return all_chunks


# ---------------------------------------------------------------------------
# 5. INSPECTION
# ---------------------------------------------------------------------------

def inspect_chunks(all_chunks: list, n: int = 5):
    import random
    sample = random.sample(all_chunks, min(n, len(all_chunks)))

    print("\n" + "=" * 60)
    print("CHUNK QUALITY INSPECTION")
    print("=" * 60)

    for i, record in enumerate(sample, 1):
        text = record["text"]
        print(f"\n--- Chunk {i} ---")
        print(f"Source       : {record['source']}")
        print(f"Review index : {record['review_index']}")
        print(f"Chunk index  : {record['chunk_index']}")
        print(f"Length       : {len(text)} chars")
        print(f"Text         : {text}")

        issues = []
        if len(text) < 80:
            issues.append("⚠️  TOO SHORT — likely a fragment")
        if re.search(r"<[^>]+>", text):
            issues.append("❌  HTML TAG — cleaning missed it")
        if re.search(r"&[a-z]+;|&#\d+;", text):
            issues.append("❌  HTML ENTITY — unescape didn't run")
        if text and text[0].islower():
            issues.append("⚠️  STARTS MID-SENTENCE")
        if text and text[-1] not in ".!?\"'":
            issues.append("⚠️  ENDS MID-SENTENCE")
        if len(text) > 550:
            issues.append("⚠️  TOO LONG — may dilute retrieval")

        if issues:
            for issue in issues:
                print(f"  {issue}")
        else:
            print("  ✅ Looks good")


# ---------------------------------------------------------------------------
# 6. MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Ingestion Pipeline — Lehman CS Professor Reviews")
    print(f"Chunk size : {CHUNK_SIZE} chars | Overlap : {OVERLAP} chars")
    print("=" * 60)

    chunks = run_pipeline(RAW_DOCUMENTS, debug=True)

    output_path = "chunks.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for record in chunks:
            f.write(json.dumps(record) + "\n")

    print("=" * 60)
    print(f"Total chunks : {len(chunks)}")
    print(f"Saved to     : {output_path}")
    print("=" * 60)

    inspect_chunks(chunks, n=5)
