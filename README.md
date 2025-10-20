# Interactive Course Data Processing

Professional data processing toolkit for converting multimedia course materials (video, audio, PDFs, and subtitles) into aligned, searchable, and visual-rich educational content.

This repository contains services and utilities used to:
- Extract and process transcripts (SRT / audio)
- Generate structured paragraphs and keywords via LLMs
- Extract visuals from PDFs and images and detect copyright status
- Align paragraphs and visuals with video timestamps and individual word timestamps
- Map processed content into storage-ready models for downstream consumption (interactive DB)

## Table of contents
- [Project overview](#project-overview)
- [Architecture and components](#architecture-and-components)
- [Features & Agents documentations](#features)
- [Example LLM prompts (excerpts)](#example-llm-prompts-excerpts)
- [Installation](#installation)
- [How the Data Processing service works](#how-the-data-processing-service-works)
- [API / usage examples](#api--usage-examples)
- [Contributing](#contributing)

## Project overview

This project is a backend service focused on converting educational media into structured, interactive content. It integrates:
- Transcription (word-level timestamps)
- LLM-powered paragraph and visual-generation
- Image processing and reverse-search (including copyright detection)
- Storage and mapping into an interactive database

Primary target use-cases:
- Turn lecture recordings + slides into time-aligned, keyword-indexed content
- Find and attach visuals (tables, charts, images) to specific timestamps/words in transcripts
- Prepare content for interactive playback, quizzes, or rich media viewers

## Architecture and components

Top-level directories of interest (src/):
- `src/services` — core business logic and orchestration (transcription, LLM, image processing, data mapping)
- `src/repositories` — persistence layer / clients to the interactive DB
- `src/clients` — lower-level clients, e.g., interactive DB client
- `src/models` — Pydantic models / schemas used across services
- `src/routes` — API routing (FastAPI)
- `src/utils` — helper utilities

Key service files:
- `src/services/data_processing_service.py` — orchestrates the main workflows: paragraph generation, visual extraction/matching, timestamp alignment, and final mapping.
- `src/services/transcription_sevice.py` — responsible for aligning paragraphs to media (word timestamps).
- `src/services/llm_service.py` — wrapper to format and call LLMs and parse responses.
- `src/services/image_service.py` — handles image search and copyright detection.

## Features

This project bundles a set of focused features for creating interactive, media-aligned educational content. The features are implemented as services and orchestrated in `DataProcessingService`.

- Transcript & subtitle processing
  - Parse SRT files, extract plain text, and prepare transcripts for LLM processing (`SRTService`).
- Paragraph generation (LLM-backed)
  - Split transcripts into small, semantically-cohesive paragraphs and extract keywords.
  - Generate a required visual suggestion for each paragraph (chart/table/image) using the generation agent.
- Word-level alignment
  - Align paragraphs to media files to produce paragraph start/end times and word-level timestamps via `TranscriptionService`.
- Visual extraction & processing
  - Extract images from PDFs (`FileProcessingService`) and run image analysis and reverse-image-search (`ImageProcessingService`).
- Copyright-aware visual handling
  - Optionally run copyright detection on extracted visuals to determine whether to store original search URLs or persistent copies.
- Visual-to-word mapping
  - Match visual start sentences provided by agents to word-level timestamps inside aligned paragraphs to compute precise visual start times.
- Mapping to storage-ready models
  - Map processed paragraphs, words, keywords and visual data to `MappedEducationalContent` for persistence in the interactive DB.

### Agents (detailed)

The system uses three primary agent modes. Each agent mode corresponds to a different user intent and processing pipeline. The code exposes these modes as `AgentMode` values and switches behavior across the following endpoints.

1) Generation agent (Generation / `AgentMode.GENERATE`)
   - Purpose: Fully synthesize paragraph structure and visuals from transcript only (no external assist files).
   - Where used: `generate_paragraphs_with_visuals` flow and `/content/generate-async` and `/content/process-async` when `agent_mode=GENERATE`.
   - LLM interaction: `LLMService.ask_search_agent` is used to run a search-enabled agent that may consult web search tools to find realistic image URLs and generate mock chart/table data.
   - Inputs:
     - `script` (full transcript text)
     - prompts: `ParagraphWithVisualPrompt.SYSTEM_PROMPT` / `ParagraphWithVisualPrompt.USER_PROMPT`
     - output schema: `LLMParagraphList`
   - Expected output:
     - Structured paragraphs including: paragraph_index, paragraph_text, keywords, and exactly one visual per paragraph (with start_sentence for mapping).
   - Notes and behaviour:
     - Distribution rules enforced by prompt: ~80% charts, ~10% tables, ~10% images.
     - The search agent may return real image URLs; the service validates/massages these into `SearchAgentVisualContent` when mapping.

2) Search agent (Assist-file-driven mapping / `AgentMode.ALWAYS_SEARCH`)
   - Purpose: When provided an assist file (PDF), extract visuals from the file and have the LLM align those extracted visuals with the transcript paragraphs.
   - Where used: `extract_and_align_pdf_visuals` flow and `/content/search-async` endpoint.
   - LLM interaction: `LLMService.ask_openai_llm` with `ParagraphAlignmentWithVisualPrompt` (the service prepares `provided_visuals` from the extracted visuals and asks the LLM to map them to paragraphs).
   - Inputs:
     - `script` (full transcript text)
     - `provided_visuals` (list of VisualMapping objects generated from extracted visuals)
     - output schema: `LLMVisualAlignmentResult`
   - Expected output:
     - Paragraphs referencing visual indices (`visual_reference`) that the service then resolves to real `StoredVisualContent` entries.
   - Notes and behaviour:
     - This mode uses the actual assets extracted from the PDF and therefore avoids inventing visuals. It ensures visuals are exact matches to the assist file.

3) Search-with-copyright agent (`AgentMode.SEARCH_FOR_COPYRIGHT`)
   - Purpose: Same as Search agent but with an additional copyright-detection step to decide whether images should be stored as protected (keep search URL) or copied into storage.
   - Where used: `extract_and_align_pdf_visuals_with_copyright_detection` flow and `/content/search-with-copyright-async` endpoint.
   - LLM / image service interaction:
     - `ImageProcessingService.search_images_with_copyright_detection` is used to return visuals annotated with `is_protected` flags.
     - LLM alignment uses the copyright-aware prompt (`ParagraphAlignmentWithVisualPrompt` for alignment, and `ImageDescriptionWithCopyrightPrompt` for image analysis earlier in the pipeline).
   - Inputs:
     - `script` (full transcript text)
     - `provided_visuals` (copyright-aware visual descriptors)
   - Expected output and behaviour:
     - Copyright-aware stored visuals keep `is_protected` set and maintain original `searched_image_url` in storage; public/non-protected visuals are replaced with stored URLs.
     - Charts and tables are always treated as non-protected.

Common error modes across agents
 - Mismatched paragraph counts between LLM output and media alignment will raise an Exception; the calling route should handle retries / user messaging.
 - Missing PDF type in the interactive DB will raise a ValueError during assist-file storage.

---

## Example LLM prompts (excerpts)

Below are the core prompt templates used by the `LLMService`. They are defined in `src/constants.py` and are used by the data processing flows to:
- create structured paragraph outputs with visuals,
- parse and structure agent outputs, and
- describe and classify images extracted from PDFs (with optional copyright detection).

Note: Prompts below use placeholders such as `{script}`, `{provided_visuals}`, and `{output_schema}` which the service replaces at runtime.

1) ParagraphWithVisualPrompt (system prompt excerpt)

```
You are an expert in **educational content design, instructional design, and video learning experiences**.
You will receive a **script text**,
## Your Task

1. **Paragraph Division**
   - Divide the full text into small paragraphs, each paragraph about 2 or maximum 3 sentences.
   - Group related ideas naturally.
   - Ensure saving the original text without any changes, summarizing or paraphrasing.
   - Ensure return all text, do NOT omit any part of the original script.

2. **Structured Output**
   - For each paragraph, create a structured object following the schema at the end of this prompt.
   - Each paragraph object MUST include: paragraph_index, paragraph_text, keywords, and exactly one visual.

3. **Keywords & OST Extraction**
   - Extract keywords, numbers, names, dates, callouts, and warnings.
   - Classify each keyword with `type` (`main`, `Key Terms`, `Callouts`, `Warnings`).

4. **Visuals (VAK Model Integration)**
   - Every paragraph MUST have exactly one visual of type: "chart", "table", or "image".
   - Distribution requirement: 80% charts, 10% tables, 10% images.

Validation rules are strict: the output must follow the JSON schema passed in `{output_schema}` and contain no extra text.
```

2) ParagraphAlignmentWithVisualPrompt (system prompt excerpt)

```
You are an expert in educational content design. You will receive:
  1) script_text: a full lesson/script to process.
  2) provided_visuals: an array of visual objects with a visual index and description. These are the ONLY visuals you may use.

Your Task:
  - Divide the text into paragraphs (2-3 sentences each) and assign exactly one provided visual to each paragraph.
  - Use each visual exactly once; do NOT invent visuals.
  - Output must strictly follow the provided `{output_schema}`.
```

3) ImageDescriptionPrompt / ImageDescriptionWithCopyrightPrompt (system prompt excerpt)

```
You are an AI assistant specialized in analyzing images extracted from PDF documents.
You will receive an image and a provided general_topic parameter.
Your task is to classify the image (chart/table/image), parse chart/table data if present, provide a concise description (<=350 chars), and return a structured response following {output_schema}.
If using the copyright-aware prompt, also assess `is_protected` based on heuristics (logos, professional photography, watermarks, etc.).
```

How prompts are used in code
- The service calls `LLMService.format_prompt` to combine system and user message templates and then either:
  - `LLMService.ask_search_agent` (uses a react agent with a search tool for web lookups and then post-processes the agent output into the expected JSON schema), or
  - `LLMService.ask_openai_llm` (directly calls the LLM and requests structured output matching a Pydantic model schema).

---
## Installation

Requirements (from repository): Python 3.11+ (see pyproject.toml / requirements.txt)

1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the FastAPI app (if available via `main.py` or an ASGI entrypoint)

```bash
# Example using uvicorn (adjust module path if different)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Use the routes under `src/routes` to interact with services (upload SRT, video, PDF).

4. Or you can run project with Docker using docker file

---
## How the Data Processing service works

The `DataProcessingService` in `src/services/data_processing_service.py` implements high-level workflows:

- generate_paragraphs_with_visuals: ingest SRT and media, call LLM to generate paragraphs with suggested visuals, align paragraphs to the media timestamps, map visuals to word timestamps, and return a storage-ready structure.
- extract_and_align_pdf_visuals: extract images from a provided PDF, run image search over extracted images, call the LLM to map visuals to paragraphs, align with video timestamps and return mapped content.
- extract_and_align_pdf_visuals_with_copyright_detection: same as above but uses copyright-aware image search and logic to decide when to use original URLs vs stored/derived assets.

It relies on collaborators (injected services / repositories):
- TranscriptionService — provides word-level timestamps and paragraph alignment
- SRTService — extracts plain text from SRT files
- LLMService — formats prompts and calls either a search agent or an LLM to generate paragraph and visual alignment outputs
- ImageProcessingService — extracts images and runs reverse-search/copyright checks
- FileProcessingService — extracts images from PDF files
- InteractiveDBRepository — stores videos, assist files, and images and exposes lookup endpoints for mapping types

---
## API / usage examples

Examples are in `src/routes` and consume the service methods above. Typical flow:

1. Upload SRT and video
2. Optionally upload a PDF (for PDF visual extraction flows)
3. Call the appropriate route which will return mapped educational content ready for persistence

---

## Contributing

1. Fork the repository
2. Create a topic branch per feature or fix
3. Open a PR with a clear description of changes


---
