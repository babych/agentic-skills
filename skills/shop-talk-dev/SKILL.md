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
   - Prefer simple, concrete words over academic or high-register vocabulary:
     - Use *call* or *use* instead of *leverage* / *utilize*.
     - Use *raw pixel bytes* instead of *decompressed packed buffer*.
     - Use *creates a texture from bytes* instead of *initiates GPU upload pipeline*.
     - Use *test data* or *fake data* instead of *synthetic sine cluster*.
     - Use *matrix data* instead of *sparse CSR/Yale notation structure*.

3. **Anti-AI Formatting Patterns**
   - **No nested bold-colon bullet spam**: Avoid `1. **Feature:** Description of feature... 2. **Next Feature:**...`
   - **No preamble or recap fluff**: Cut sentences like *"In order to provide developers with a streamlined experience..."* or *"By leveraging this approach, users can effortlessly..."*
   - Keep introductory sentences to 1 or 2 lines maximum.

4. **Concrete Code Symbols & Exact Paths**
   - Always reference the real file paths (`shaders/prpd_from_atlas.frag`), method names (`convertYaleToFlat()`), and variables rather than vague abstractions.
   - Code examples must be copy-paste ready, stateful where necessary (avoiding naive builder traps), and reflect how the project actually uses the API.

5. **Changelog / Release Notes Standard**
   - Imperative mood (*"Fix...", "Add...", "Clean up..."*).
   - Use the wording from the actual ticket or bug report whenever possible, rather than rewriting it with fancy synonyms.
   - Include the exact formula, variable, or error when explaining a fix (e.g. `(u_colormap + 0.5) / 256.0`, `FlutterFragCoord().xy`, guard `log2(0)`).
