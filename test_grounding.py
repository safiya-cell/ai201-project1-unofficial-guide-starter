"""
test_grounding.py — End-to-end grounding verification
Tests that every answer is traceable to retrieved chunks, not LLM training data.

Run with:  python test_grounding.py
"""

import os
from dotenv import load_dotenv
from groq import Groq

from embed_and_retrieve import load_chunks, get_collection, embed_and_store, retrieve
from app import generate, build_prompt, format_sources, SYSTEM_PROMPT

load_dotenv()

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

TOP_K     = 5
MAX_SCORE = 0.65

CHUNKS_FILE = "chunks.jsonl"
CHROMA_DIR  = "chroma_store"

# ---------------------------------------------------------------------------
# TEST QUERIES
# Three grounded queries your docs cover + one out-of-scope query
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "id":       "grounded_1",
        "query":    "What do students say about professor 624955 lectures?",
        "expect":   "grounded",
        "note":     "Directly covered — reviews mention interactive lectures.",
    },
    {
        "id":       "grounded_2",
        "query":    "Which professors are hard to follow during lectures?",
        "expect":   "grounded",
        "note":     "Covered — prof_487824 reviews mention unclear lectures.",
    },
    {
        "id":       "grounded_3",
        "query":    "What do students say about office hours?",
        "expect":   "grounded",
        "note":     "Covered — multiple reviews mention office hours.",
    },
    {
        "id":       "out_of_scope",
        "query":    "What is the parking situation at Lehman College?",
        "expect":   "no_info",
        "note":     "NOT in any review — model must say it doesn't know.",
    },
    {
        "id":       "out_of_scope_2",
        "query":    "What GPA do you need to get into the CS program at Lehman?",
        "expect":   "no_info",
        "note":     "Admissions info — not in professor reviews.",
    },
]

# Phrases the model should use when it has no information
NO_INFO_PHRASES = [
    "don't have enough information",
    "do not have enough information",
    "not enough information",
    "no information",
    "not mentioned",
    "not covered",
    "cannot answer",
    "can't answer",
    "documents don't",
    "documents do not",
    "not in the",
    "no reviews",
]

# Red-flag phrases that suggest the model is drawing on training data
HALLUCINATION_SIGNALS = [
    "generally",
    "typically",
    "in most cases",
    "it is common",
    "many professors",
    "most cs professors",
    "usually",
    "as with most",
    "based on my knowledge",
    "from my training",
]


# ---------------------------------------------------------------------------
# GROUNDING CHECKER
# ---------------------------------------------------------------------------

def check_grounding(answer: str, retrieved: list[dict]) -> dict:
    """
    Heuristic checks to detect grounding failures.
    Returns a dict with pass/fail flags and reasoning.
    """
    answer_lower = answer.lower()
    results = {}

    # Check 1: Does the answer mention any source?
    source_ids = [r["source"] for r in retrieved]
    mentioned_sources = [s for s in source_ids if s in answer]
    results["cites_source"]     = len(mentioned_sources) > 0
    results["cited_sources"]    = mentioned_sources

    # Check 2: Does the answer contain hallucination signal phrases?
    flagged_phrases = [p for p in HALLUCINATION_SIGNALS if p in answer_lower]
    results["hallucination_risk"]    = len(flagged_phrases) > 0
    results["flagged_phrases"]       = flagged_phrases

    # Check 3: Is any chunk text actually reflected in the answer?
    chunk_words_found = []
    for r in retrieved:
        # Take key phrases (5+ word windows) from chunk and check presence
        words = r["text"].split()
        for i in range(len(words) - 3):
            phrase = " ".join(words[i:i+4]).lower().strip(".,!?")
            if phrase in answer_lower:
                chunk_words_found.append(phrase)
                break
    results["answer_reflects_chunks"] = len(chunk_words_found) > 0
    results["matching_phrases"]        = chunk_words_found[:3]

    return results


def check_no_info_response(answer: str) -> bool:
    """Check that out-of-scope queries get a proper 'no info' response."""
    answer_lower = answer.lower()
    return any(phrase in answer_lower for phrase in NO_INFO_PHRASES)


# ---------------------------------------------------------------------------
# RUNNER
# ---------------------------------------------------------------------------

def run_tests():
    print("=" * 65)
    print("GROUNDING TEST — Lehman CS Professor RAG Pipeline")
    print("=" * 65)

    # Init
    chunks     = load_chunks(CHUNKS_FILE)
    collection = get_collection(CHROMA_DIR)
    embed_and_store(chunks, collection)

    passed = 0
    failed = 0
    warnings = 0

    for tc in TEST_CASES:
        print(f"\n{'─'*65}")
        print(f"TEST  : {tc['id']}")
        print(f"QUERY : {tc['query']}")
        print(f"EXPECT: {tc['expect']} — {tc['note']}")
        print()

        # Retrieve
        retrieved = retrieve(tc["query"], collection, top_k=TOP_K)
        retrieved = [r for r in retrieved if r["score"] <= MAX_SCORE]

        # Print retrieved sources and scores
        if retrieved:
            print("  Retrieved chunks:")
            for r in retrieved:
                print(f"    [{r['rank']}] {r['source']} score={r['score']} — {r['text'][:80]}...")
        else:
            print("  No chunks passed the score threshold.")
        print()

        # Generate
        answer = generate(tc["query"], retrieved)
        print(f"  Answer:\n  {answer}\n")

        # Evaluate
        if tc["expect"] == "no_info":
            ok = check_no_info_response(answer)
            if ok:
                print("  ✅  PASS — model correctly said it doesn't have enough info")
                passed += 1
            else:
                print("  ❌  FAIL — model should have said 'I don't have enough information'")
                print("       This is a grounding failure: the model answered from training data.")
                failed += 1

        elif tc["expect"] == "grounded":
            checks = check_grounding(answer, retrieved)

            test_passed = True

            if checks["cites_source"]:
                print(f"  ✅  Cites source(s): {checks['cited_sources']}")
            else:
                print("  ⚠️   No source citation found in answer")
                warnings += 1
                test_passed = False

            if not checks["hallucination_risk"]:
                print("  ✅  No hallucination signal phrases detected")
            else:
                print(f"  ❌  Hallucination risk — flagged phrases: {checks['flagged_phrases']}")
                failed += 1
                test_passed = False

            if checks["answer_reflects_chunks"]:
                print(f"  ✅  Answer reflects chunk content: {checks['matching_phrases']}")
            else:
                print("  ⚠️   Could not verify answer traces to retrieved chunks")
                warnings += 1

            if test_passed:
                passed += 1

    # Summary
    total = len(TEST_CASES)
    print(f"\n{'='*65}")
    print(f"RESULTS: {passed}/{total} passed  |  {failed} failed  |  {warnings} warnings")
    print(f"{'='*65}")

    if failed == 0:
        print("✅  All grounding checks passed.")
    else:
        print("❌  Grounding failures found — tighten your system prompt or")
        print("    check that retrieved chunks are passing the score threshold.")

    if warnings > 0:
        print(f"⚠️   {warnings} warning(s) — answer may be grounded but source")
        print("    citations were not detected inline. Check your system prompt.")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_tests()
