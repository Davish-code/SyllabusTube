# SyllabusTube

> Turn your syllabus PDF into a verified, topic-mapped YouTube playlist.

## Status

Phase 0 (Skeleton & Infrastructure) and Phase 1 (PDF Ingestion & Syllabus Structuring) are complete.

- **Phase 0**: Architecture, configuration schemas, typed domain models, thread-safe SQLite caching, quota tracking, CLI skeleton.
- **Phase 1**: PyMuPDF extraction, Gemini vision OCR for scanned pages, LLM structuring into Modules/Topics, schema validation & auto-repair, and caching.

## Bring Your Own Keys (BYO-Keys)

SyllabusTube runs entirely on your infrastructure and uses your own API keys:
- **Google Gemini API Key**: Used for syllabus structuring, OCR fallback, and topic verification. Set `GEMINI_API_KEY` in `.env`.
- **YouTube Data API v3 Key**: Used for playlist and video metadata discovery.
- **Google OAuth Desktop Credentials (`client_secret.json`)**: Required only when exporting curated playlists directly to your YouTube account.

### Privacy & Data Safety
SyllabusTube processes your files locally. Your syllabus PDF is never uploaded to third-party databases or analytics services; it is transmitted solely to your own configured LLM provider endpoint (Google Gemini or your local Ollama server) for structuring.

## Installation

Requires Python 3.11+.

```bash
# Clone the repository
git clone https://github.com/your-username/syllabustube.git
cd syllabustube

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install package in editable mode
pip install -e .
```

*Note: No system-level binaries or OCR libraries (such as Tesseract) are required. Scanned or image-only pages are automatically processed via Gemini Vision.*

## Setup & Verification

1. Copy the example environment file and add your keys:
   ```bash
   cp .env.example .env
   ```
2. See [Google Cloud Setup Guide](docs/setup_google_cloud.md) to generate your API keys and download `client_secret.json`.
3. Verify your environment setup:
   ```bash
   python main.py --check-setup
   ```

## Usage

### Phase 1: Ingest & Structure Syllabus
Extract text from a syllabus PDF, perform OCR on scanned pages, structure modules and topics via LLM, and save JSON:

```bash
# Ingest PDF and output structured JSON to output/<stem>.syllabus.json
python main.py path/to/syllabus.pdf --stage ingest

# Provide explicit subject or university hints
python main.py path/to/syllabus.pdf --stage ingest --subject "Discrete Mathematics" --university "Stanford"

# Load an existing structured syllabus JSON directly
python main.py --syllabus-json output/syllabus.syllabus.json

# Run with verbose debug logging
python main.py path/to/syllabus.pdf --stage ingest --verbose
```

## Roadmap

- [x] **Phase 0**: Architecture, configuration validation, typed domain models, SQLite cache, quota tracking, CLI skeleton
- [x] **Phase 1**: PDF text extraction, OCR/vision fallback, and LLM-based syllabus structuring
- [ ] **Phase 2**: YouTube Data API v3 search planning, candidate discovery, and prefiltering
- [ ] **Phase 3**: Subtitle fetching, timestamped chapter extraction, and local Whisper fallback
- [ ] **Phase 4**: Overlapping transcript chunking, dense vector embeddings, and BM25 index
- [ ] **Phase 5**: Hybrid retrieval, cross-encoder reranking, and LLM verification with evidence citations
- [ ] **Phase 6**: Multi-objective playlist scoring and greedy set-cover curriculum optimization
- [ ] **Phase 7**: Alignment reporting (Markdown/JSON) and authenticated YouTube playlist export
- [ ] **Phase 8**: Web application and REST API server (`server/` and `ui/`)
- [ ] **Phase 9**: Evaluation harness against gold-standard curricula (`eval/`)

## License

This project is licensed under the [MIT License](LICENSE).
