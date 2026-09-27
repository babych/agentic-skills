---
name: book-translator-publisher
description: >-
  End-to-end pipeline for translating, typesetting, illustrating, and publishing large historical and scientific books.
  Combines Typst publishing, Gemini Flash Lite batch translation, Gemini Vision illustration auditing, and dynamic index generation.
---

# Book Translator & Publisher Pipeline

A complete, production-tested methodology and toolset for turning raw scanned books or large multilingual manuscripts into publication-ready, beautifully typeset PDF books using **Typst** and **Google Gemini Flash Lite**.

---

## 🏗️ The 5 Pillars of the Pipeline

```
[1. Scan & Text Preprocessing]
           │
           ▼
[2. Batch Translation (Flash Lite)]  <── Checkpointing & Terminology Cache
           │
           ▼
[3. Typst Structure & Headings]      <── '=', '==', '===', Labels <idx-...>
           │
           ▼
[4. Vision Illustration Pipeline]    <── Filter Noise + Extract Real Captions
           │
           ▼
[5. Dynamic Alphabetical Index]      <── Ukrainian Collation + #context Page Refs
           │
           ▼
[Final Publication-Ready PDF]
```

---

## 1. Cost-Saving Strategy (Zero-Quota Wastage)

- **Primary Translation & Text Work**: Always use **`gemini-3.5-flash-lite`** or **`gemini-3.1-flash-lite`**. They have massive token context, fast responses, and cost virtually nothing compared to frontier models.
- **Multimodal Illustration Audits**: Downscale images to max 512–640 px before sending to Gemini Vision. This reduces token consumption by ~80% and eliminates HTTP 429 rate-limiting.
- **Checkpointing (`*_cache.json`)**: Every batch script must write results to disk after each item. Never re-process already translated or evaluated entries.
- **Polite Rate Pacing**: Add 1.2–2.0s sleep between Lite text calls and 4–8s between Vision calls.

---

## 2. Typst Architecture & Headings Standards

When formatting books in Typst:
1. **Document Setup**:
   ```typst
   #set page(paper: "a4", margin: (x: 1.8cm, top: 2.2cm, bottom: 2.2cm))
   #set text(font: "Linux Libertine", size: 10pt, lang: "uk")
   #set par(justify: true, leading: 0.65em)
   #show: rest => columns(2, rest)
   ```
2. **Hierarchy**:
   - Level 1 (`= `): Book Title, Part, or Major Alphabet Letter (A, B, C...).
   - Level 2 (`== `): Individual Article / Chapter heading. Append `<idx-slug-Lline>` for index referencing.
   - Level 3 (`=== `): Subheadings inside articles (e.g., `=== Звернення до лікаря`, `=== Методи боротьби`).
3. **Labels**:
   - For headings: `== Назва статті <idx-art-name-L123>`
   - For plain text positions: `#[] <idx-marker-L123>`

---

## 3. Intelligent Illustration Engine (Vision + Typst)

Raw OCR extraction often produces broken images (horizontal slits across 2 columns) and empty captions `caption: []`.

### The Verification Workflow:
1. **Candidate Scan**: Identify full-page plates (pages with `< 150` text characters) and two-column gaps.
2. **Vision Filter**: Ask Gemini Vision whether an image is valid:
   - **Reject (`is_valid: false`)**: Empty white/gray spaces, random horizontal divider lines, decorative initials, accidental split text.
   - **Accept (`is_valid: true`)**: Real photos, anatomical diagrams, blueprints, portraits, botanical engravings.
3. **Captioning**:
   - Transcribe embedded English captions/figure numbers (e.g. *Fig. 8*).
   - Generate professional, concise Ukrainian captions for the book:
     ```typst
     #figure(
       image("illustrations/filename.png", width: 95%),
       caption: [Рис. 8. Поперечний розріз клапана волика медоносної бджоли.]
     )
     ```

---

## 4. Dynamic Alphabetical Index Engine

Never hardcode page numbers from the original book. In Typst, pages shift due to font size, translation volume, and margins.

### Index Generation Rules:
1. **Extraction & Grouping**:
   - Capitalized entries = Main terms.
   - Indented / lowercase entries = Sub-entries (`#h(1em) `).
2. **Ukrainian Alphabetical Collation**:
   - Order: `А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я` followed by Latin and numerals.
3. **Dynamic Page Calculation**:
   - Each term maps to an article's `<label>`.
   - Typst calculates the live page at compile time:
     ```typst
     Термін #box(width: 1fr, repeat[.]) #context str(counter(page).at(<idx-label>).first())
     ```
   - Page numbers automatically align right with dot leaders (`repeat[.]`).

---

## 5. Colophon & Legal Safeguards

Always include a standardized Colophon at the end of the translated book:
- Original work attribution, authors, original year, and archive scan source.
- Model & Pipeline disclosure (Gemini Flash Lite translation, PyMuPDF, Typst).
- License (e.g., **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**).
- Explicit prohibition of commercial resale, unauthorized mass printing, or closed-source redistribution.

---

## 6. Ready-to-Use Scripts in `scripts/`

- **`scripts/index_builder.py`**: Builds, cleans, and sorts Typst dynamic indexes with dot leaders.
- **`scripts/vision_evaluator.py`**: Crops, filters noise, and generates rich captions via Gemini Vision.
- **`scripts/batch_translate.py`**: Translates book chunks with resume capability and term preservation.
