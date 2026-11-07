# Architecture & Pipeline Design

SyllabusTube transforms unstructured course syllabus PDFs into an organized, verified, and cohesive YouTube video course.

## The 9-Step Pipeline

```
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │ 1. Ingest &     │ ───>  │ 2. Discover     │ ───>  │ 3. Enrich       │
  │    Structure    │       │    Candidates   │       │    Transcripts  │
  └─────────────────┘       └─────────────────┘       └─────────────────┘
           │                         │                         │
           v                         v                         v
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │ 4. Chunk &      │ ───>  │ 5. Retrieve &   │ ───>  │ 6. Verify with  │
  │    Index        │       │    Rerank       │       │    LLM Evidence │
  └─────────────────┘       └─────────────────┘       └─────────────────┘
           │                         │                         │
           v                         v                         v
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │ 7. Set-Cover    │ ───>  │ 8. Alignment &  │ ───>  │ 9. Benchmark &  │
  │    Selection    │       │    Export       │       │    Evaluation   │
  └─────────────────┘       └─────────────────┘       └─────────────────┘
```

### 1. Ingest & Structure
- Extracts text from digital or scanned PDFs via `pypdf`/`pdfplumber`.
- Falls back to Gemini multimodal vision for low-DPI or non-extractable scans.
- An LLM parses unformatted course text into a typed hierarchy: Course $\rightarrow$ Modules $\rightarrow$ Topics (with learning objectives and educational depth: intro, university, or advanced).

### 2. Discover Candidates
- A query planner extracts targeted search terms per module.
- Queries YouTube Data API v3 (`search().list(type='playlist')` and `type='video'`).
- Optional `yt-dlp` scraping backend provides quota-free search discovery.
- Prefilters candidates: removes stale videos (>5 years by default), shorts (<3 min), multi-hour streams (>3 hrs), and non-matching languages.

### 3. Enrich Transcripts & Chapters
- Fetches official and auto-generated subtitle tracks via `youtube-transcript-api`.
- Extracts timestamped chapters from video descriptions.
- Optional local OpenAI Whisper fallback transcribes key videos lacking public captions.

### 4. Chunk & Index
- Splits video transcripts into overlapping sliding-window chunks (default 150 words, 30-word overlap) preserving start/end timestamps.
- Indexes chunks into two complementary search structures:
  - **Dense vector store** (ChromaDB or SQLite embeddings) using text embeddings.
  - **Sparse keyword index** (BM25) for exact technical terms, formulas, and theorem names.

### 5. Hybrid Retrieval & Rerank
- Retrieves top-$k$ candidates for each topic using hybrid retrieval.
- Combines dense semantic similarity and BM25 sparse scores via Reciprocal Rank Fusion (RRF).
- Cross-encoder rerankers rescore the top candidates.

### 6. LLM Verification & Evidence Check
- For candidate matches exceeding the review threshold, an LLM evaluator reads the topic objective and the exact transcript excerpt.
- Assigns a verdict (`yes`, `partial`, `no`), extracts an exact quotation as proof, and assigns a calibrated confidence score.
- Categorizes matches into tiers:
  - **High**: Confident, direct coverage of the topic.
  - **Review**: Partial coverage or lower confidence; suggested for manual review.
  - **Gap**: No satisfactory video found; explicitly reported as a syllabus gap.

### 7. Multi-Objective Set-Cover Selection
- Avoids stitching together disconnected single videos from 30 different channels.
- Evaluates candidate playlists across four weighted dimensions:
  - **Coverage**: Number of syllabus topics addressed.
  - **Focus**: Ratio of relevant videos to off-topic videos in the playlist.
  - **Order**: Alignment between playlist progression and syllabus module sequence.
  - **Quality**: Channel reputation, like/view ratio, and transcript clarity.
- Executes greedy set-cover optimization to select at most $N$ playlists (default 3) that maximize syllabus coverage.

### 8. Alignment Reporting & YouTube Export
- Emits a comprehensive Markdown and JSON report displaying covered topics, matched timestamps, and flagged syllabus gaps.
- Authenticates via Google OAuth 2.0 Desktop client.
- Automatically creates an unlisted playlist on the user's YouTube channel and populates it with ordered videos.

### 9. Benchmark & Evaluation
- Compares recommendations against labeled gold datasets (`eval/gold/`).
- Computes Precision@K, Recall, F1 score, and Topic Coverage.

---

## Quota Costs & Budgeting

The default YouTube Data API v3 quota allocation is **10,000 units/day**, resetting at midnight Pacific Time (PT).

| Operation | Cost (units) | Optimization Strategy |
|---|---|---|
| `search().list` | 100 | Run queries at module-level (not per-topic). Use `yt-dlp` fallback when quota is scarce. |
| `videos().list` / `playlistItems().list` | 1 | Batch up to 50 IDs per request. |
| `playlists().insert` | 50 | 1 call per generated course playlist. |
| `playlistItems().insert` | 50 | 1 call per video added during export. Export formula: $50 + (50 \times N)$. |

### Conservation Rules
1. **SQLite Entity Cache**: Caches playlists, video metadata, and transcripts with configurable TTL. Repeated runs on the same subject consume zero discovery quota.
2. **Batching**: Never issue single-item detail requests; batch up to 50 items.
3. **Budget Tracker**: `QuotaTracker` enforces the daily ceiling, rejects operations that would breach limits, and exposes real-time remaining quota.

---

## Evaluation Methodology

Benchmark test suites are stored in `eval/gold/<subject>/`:
- `syllabus.pdf`: Original course syllabus document.
- `labels.json`: Hand-verified ground-truth mapping topics to valid YouTube video IDs.

Metrics:
$$\text{Precision} = \frac{|\text{Retrieved} \cap \text{Gold}|}{|\text{Retrieved}|}$$
$$\text{Recall} = \frac{|\text{Retrieved} \cap \text{Gold}|}{|\text{Gold}|}$$
$$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$
$$\text{Coverage} = \frac{|\text{Topics with High-Tier Match}|}{|\text{Total Topics}|}$$

