# SyllabusTube

> Turn your syllabus PDF into a verified, topic-mapped YouTube playlist.

## Status

Phase 0 complete. The architecture, configuration schemas, typed domain models, thread-safe SQLite caching, quota tracking, and CLI skeleton are implemented. Subsequent phases implement ingestion, discovery, retrieval, verification, and export.

## Bring Your Own Keys (BYO-Keys)

SyllabusTube runs entirely on your infrastructure and uses your own API keys:
- **Google Gemini API Key**: Used for syllabus structuring, OCR fallback, and topic verification.
- **YouTube Data API v3 Key**: Used for playlist and video metadata discovery.
- **Google OAuth Desktop Credentials (`client_secret.json`)**: Required only when exporting curated playlists directly to your YouTube account.

Keys are loaded from `.env` and local credentials files; they are never logged or committed to version control.

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

```bash
# Process a course syllabus (CLI entrypoint)
python main.py path/to/syllabus.pdf

# Run with verbose debug logging
python main.py path/to/syllabus.pdf --verbose

# Run diagnostics
python main.py --check-setup
```

## Roadmap

- [x] **Phase 0**: Architecture, configuration validation, typed domain models, SQLite cache, quota tracking, CLI skeleton
- [ ] **Phase 1**: PDF text extraction, OCR/vision fallback, and LLM-based syllabus structuring
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

