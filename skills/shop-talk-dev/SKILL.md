---
name: shop-talk-dev
description: >-
  Writes and edits technical documentation, READMEs, CHANGELOGs, PRs, and commit
  messages in a pragmatic, human dev-to-dev (shop talk / kernel) style. Eliminates
  AI-generated fluff, marketing adjectives, over-structured bullet outlines, and
  textbook jargon. Use when the user requests simple, plain, non-native friendly,
  or human developer documentation.
---

# Shop Talk / Human Dev Style

This skill defines how to write documentation, READMEs, changelogs, commit messages, and PR descriptions so they sound like an authentic software engineer talking directly to another engineer.

## Core Principles

1. **Dev-to-Dev Directness ("Shop Talk")**
   - Write like an engineer explaining something on Slack or a PR review.
   - Zero marketing adjectives: ban words like "seamless", "cutting-edge", "robust", "lightning-fast", "tailored", "pivotal", "boasts", "comprehensive".
   - State what the component is, what data it takes, and how to call it. Nothing else.

2. **Simple Words for Non-Native English Readers**
   - Many developers reading the docs are not native English speakers.
   - Prefer simple, concrete words over academic, textbook, or high-register vocabulary:
     - Use *call* or *use* instead of *leverage* / *utilize*.
     - Use *raw bytes* instead of *decompressed packed buffer payload*.
     - Use *send to server* / *upload* instead of *initiate transport egress pipeline*.
     - Use *test data* or *dummy data* instead of *synthetically generated stochastic fixtures*.
     - Use *grid* or *table* instead of *multi-dimensional indexed tensor array structure*.
     - Use *fix crash on null* instead of *mitigate anomalous dereferencing faults*.

3. **Anti-AI Formatting Patterns**
   - **No nested bold-colon bullet spam**: Avoid repetitive mechanical lists like:
     - `**Feature:** Description...`
     - `**Benefit:** Description...`
     - `**Capability:** Description...`
   - **No preamble or recap fluff**: Cut sentences like:
     - *"In order to provide developers with a streamlined experience..."*
     - *"By leveraging this cutting-edge approach, users can effortlessly..."*
     - *"It is important to note that..."*
   - Keep introductory sentences to 1 or 2 lines maximum.

4. **Concrete Code Symbols & Exact References**
   - Always reference exact file paths, real method/function names, and flags rather than hand-waving abstractions.
   - Code snippets must be copy-paste ready, stateful where necessary, and free of unnecessary pseudo-code placeholders.

5. **Changelog / PR / Commit Message Standards**
   - Imperative mood (*"Fix...", "Add...", "Clean up...", "Drop..."*).
   - State the problem, the root cause, and the exact solution in 1–3 short sentences.
   - Use the wording from the actual ticket or error output whenever possible, rather than inventing elaborate synonyms.
   - Include the exact variable name, config flag, status code, or formula when explaining a fix.
