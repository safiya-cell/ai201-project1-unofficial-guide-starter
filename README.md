# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

The domain is Student reviews of CS professors at Lehman College. This is difficult for official channels because they do not show the teaching style, class difficulty, and other students' experiences with their professors. 

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source           | Type | URL or file path                                 |
|---|------------------|------|--------------------------------------------------|
| 1 | Rate My Professor|Review|https://www.ratemyprofessors.com/professor/3014815|
| 2 | Rate My Professor|Review|https://www.ratemyprofessors.com/professor/1847213|
| 3 | Rate My Professor|Review|https://www.ratemyprofessors.com/professor/457502 |
| 4 | Rate My Professor|Review|https://www.ratemyprofessors.com/professor/2418146|
| 5 | Rate My Professor|Review|https://www.ratemyprofessors.com/professor/3013308|
| 6 | Rate My Professor|Review|https://www.ratemyprofessors.com/professor/2412165|
| 7 | Rate My Professor|Review|https://www.ratemyprofessors.com/professor/624955 |
| 8 | Rate My Professor|Review|https://www.ratemyprofessors.com/professor/487824 |
| 9 | Rate My Professor|Review|https://www.ratemyprofessors.com/professor/1973094|
| 10| Rate My Professor|Review|https://www.ratemyprofessors.com/professor/2668831|

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size: 512 characters**

**Overlap: There will be overlap as it will cut across sentences**

**Why these choices fit your documents: it is based on a review that has smaller amounts of characters. This is when fixed size chunking is the best approach to splitting characters**

**Final chunk count: 512**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used: all-MiniLM-L6-v2 via sentence-transformers**

**Production tradeoff reflection: There would be context length limits and it would not run locally if i weigh in choosing a different model**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 |What do students say about the professors' teaching at the college? | some of the professors teach well while others are challenging | One of the more organized professors in the department. Highly interactive lectures. Students who attend every class do significantly better on exams. | relevant | accurate
| 2 |What are students saying about the teachers' personalities? | described as easy-going and helpful | One of the more organized professors in the department. Highly interactive lectures. Students who attend every class do significantly better on exams. | off-target | inaccurate|
| 3 |What makes students want to take certain professors again? | they make it easy to understand concepts|One of the more organized professors in the department. Highly interactive lectures. Students who attend every class do significantly better on exams | relevant |accurate |
| 4 |What prevents students from taking certain professors again? |they make it difficult to understand concepts |One of the more organized professors in the department. Highly interactive lectures. Students who attend every class do significantly better on exams |off-target |inaccurate |
| 5 |What do students say about the assignments given? |they get alot of homework and projects and their teachers guide them | Assignments are confusing with minimal instructions. Many students rely on YouTube to learn the actual material. Feedback on work is nearly nonexistent. | relevant| accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->


**Question that failed: 
What are students saying about the teachers' personalities?
What prevents students from taking certain professors again?**

**What the system returned: One of the more organized professors in the department. Highly interactive lectures. Students who attend every class do significantly better on exams.**

**Root cause (tied to a specific pipeline stage): retrieval similarity stage where it only showed the same results for the two questions**

**What you would change to fix it: To get more results from the reviews of the professors. The amount of reviews were limited**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->
**One way the spec helped you during implementation: The number of characters used for fixed chunking helped me break up the sentences into different parts. It also helped with overlap for relevant information to be shown when being split.**

**One way your implementation diverged from the spec, and why: It split the relevant information which cut off mid sentence. This is because of the amount of characters used.**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI: I asked the AI to implement a script that loads the documents, cleans them, produces 512 characters and overlap, and adds the planning.md file.*
- *What it produced: it produced an ingest.py with the chunksize, the overlap, and the other specs in the planning.md file.*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI: generate your embedding and retrieval code. Use the diagram to establish the full architecture, then  implement the embedding step (loading chunks from your ingestion pipeline, embedding with all-MiniLM-L6-v2, storing in ChromaDB with source metadata) and a retrieval function.*
- *What it produced: it produced an embedding and retrieval file, as well as the architecture flow chart and the instructions to install the sentence transformers before running the  file on VS Code.*
- *What I changed or overrode:*
