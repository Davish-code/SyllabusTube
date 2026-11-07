# Contributing to SyllabusTube

Thank you for contributing to SyllabusTube! Follow these guidelines to maintain code quality, reproducibility, and security.

## Development Setup

1. Fork and clone the repository.
2. Create and activate a Python 3.11+ virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```
3. Install dependencies in editable mode:
   ```bash
   pip install -e .
   ```

## Code Quality Standards

Before submitting a pull request, verify that:
1. All unit tests pass:
   ```bash
   pytest
   ```
2. Formatting and linting are clean:
   ```bash
   ruff check .
   ruff format --check .
   ```
3. Every function and class includes complete type annotations and docstrings.
4. No `print()` calls are introduced outside `main.py` (use `syllabustube.utils.logging.get_logger`).

## Adding Gold Evaluation Test Cases

To contribute evaluation benchmark subjects:
1. Create a directory: `eval/gold/<subject_name>/`.
2. Add the course syllabus PDF: `eval/gold/<subject_name>/syllabus.pdf`.
3. Add the verified label file: `eval/gold/<subject_name>/labels.json` conforming to this schema:
   ```json
   {
     "subject": "Discrete Mathematics",
     "version": "1.0",
     "topics": [
       {
         "topic_id": "topic_1_1",
         "topic_name": "Propositional Logic and Truth Tables",
         "gold_video_ids": ["VIDEO_ID_HERE"],
         "acceptable_video_ids": []
       }
     ]
   }
   ```
4. Run the evaluation benchmark:
   ```bash
   python -m eval.run_eval --subject <subject_name>
   ```

## Security & Git Hygiene

- Never commit `.env`, `token.json`, `client_secret.json`, or any SQLite databases.
- Always run `git status` before committing to ensure no credentials or caches are staged.

