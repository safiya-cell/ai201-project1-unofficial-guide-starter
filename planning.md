# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

The domain is Student reviews of CS professors at Lehman College. This is difficult for official channels because they do not show the teaching style, class difficulty, and other students' experiences with their professors.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|---------------------------------------------------|
| 1 | RMP    |Review       | https://www.ratemyprofessors.com/professor/3014815| 
| 2 | RMP    |Review       |https://www.ratemyprofessors.com/professor/1847213 |
| 3 | RMP    |Review       |https://www.ratemyprofessors.com/professor/457502  |
| 4 | RMP    |Review       |https://www.ratemyprofessors.com/professor/2418146 |
| 5 | RMP    |Review       |https://www.ratemyprofessors.com/professor/3013308 |
| 6 | RMP    |Review       |https://www.ratemyprofessors.com/professor/2412165 |
| 7 | RMP    |Review       |https://www.ratemyprofessors.com/professor/624955  |
| 8 | RMP    |Review       |https://www.ratemyprofessors.com/professor/487824  |
| 9 | RMP    |Review       |https://www.ratemyprofessors.com/professor/1973094 |
| 10| RMP    |Review       |https://www.ratemyprofessors.com/professor/2668831 |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size: 152 characters**

**Overlap: There will be overlap as it will cut across sentences**

**Reasoning: Fixed-size chunking causes the overlap which is more suitable for reviews from Rate My Professor**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model: sentence-transformers all-MiniLM-L6-v2**

**Top-k:**

**Production tradeoff reflection: there would be context length limits**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question                                                           | Expected answer                        |
|---|--------------------------------------------------------------------|----------------------------------------|
| 1 | What do students say about the professors' teaching at the college?|some of the professors teach well while others are challenging|
| 2 | What are the students saying about the teachers' personalities?      |described as easy-going and helpful     |
| 3 | What makes students want to take certain professors again?         |they make it easy to understand concepts|
| 4 | What prevents students from taking certain professors again?       |they make it difficult to understand concepts|
| 5 | What do students say about the assignments given?                  |they get alot of homework and projects and their teachers guide them|

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Inconsistent documents

2. Chunks that split key information across boundaries

---

## Architecture

<img width="5317" height="515" alt="image" src="https://github.com/user-attachments/assets/afdd389f-4423-41a0-ba9f-a8878c19395d" />


---

## AI Tool Plan

     I'll give Claude my Fixed Chunking Strategy section and ask it to implement chunk_text().

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
