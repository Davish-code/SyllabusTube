"""Command-line interface for SyllabusTube."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

# Ensure src/ layout is resolvable when invoked directly without pip install -e .
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from syllabustube.config import ConfigurationError, get_config, mask_secret
from syllabustube.exceptions import SyllabusTubeError
from syllabustube.pipeline import Pipeline
from syllabustube.utils.logging import setup_logging


def check_setup(config_path: str | None = None) -> bool:
    """Run diagnostics to verify dependencies, API keys, files, and permissions.

    Returns:
        True if all required setup checks pass, False otherwise.
    """
    print("=" * 60)
    print("SyllabusTube Setup Diagnostics")
    print("=" * 60)

    results: list[tuple[str, bool, str]] = []

    # 1. Python version (>= 3.11)
    py_ver = sys.version_info
    py_ok = (py_ver.major == 3 and py_ver.minor >= 11) or py_ver.major > 3
    results.append(
        (
            "Python Version (>= 3.11)",
            py_ok,
            f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}",
        )
    )

    # 2. Config loading
    cfg = None
    try:
        cfg = get_config(config_path=config_path, reload=True)
        results.append(("Configuration Loading", True, "config.yaml validated successfully"))
    except ConfigurationError as exc:
        results.append(("Configuration Loading", False, str(exc)))

    # 3. Gemini API Key
    gemini_key = cfg.gemini_api_key if cfg else None
    if gemini_key and gemini_key.strip():
        results.append(
            ("Gemini API Key (GEMINI_API_KEY)", True, f"Configured ({mask_secret(gemini_key)})")
        )
    else:
        results.append(("Gemini API Key (GEMINI_API_KEY)", False, "Missing in .env or environment"))

    # 4. YouTube API Key
    yt_key = cfg.youtube_api_key if cfg else None
    if yt_key and yt_key.strip():
        results.append(
            ("YouTube API Key (YOUTUBE_API_KEY)", True, f"Configured ({mask_secret(yt_key)})")
        )
    else:
        results.append(
            ("YouTube API Key (YOUTUBE_API_KEY)", False, "Missing in .env or environment")
        )

    # 5. OAuth Client Secret
    oauth_file = Path(cfg.google_oauth_client_file if cfg else "client_secret.json")
    if oauth_file.exists() and oauth_file.is_file():
        results.append(("OAuth Client Secret File", True, f"Found ({oauth_file})"))
    else:
        results.append(
            (
                "OAuth Client Secret File",
                False,
                f"Missing ({oauth_file}). Required only for YouTube playlist export.",
            )
        )

    # 6. Cache DB Writable
    cache_path = Path(cfg.cache.path if cfg else "cache/syllabustube.db")
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        test_conn = sqlite3.connect(cache_path)
        test_conn.execute("CREATE TABLE IF NOT EXISTS _write_test (id INT)")
        test_conn.execute("DROP TABLE _write_test")
        test_conn.close()
        results.append(("Cache DB Writable", True, f"Writable at {cache_path}"))
    except (OSError, sqlite3.Error) as exc:
        results.append(("Cache DB Writable", False, f"Failed write test at {cache_path}: {exc}"))

    # Print checklist
    all_passed = True
    for name, status, detail in results:
        status_symbol = "[PASS]" if status else "[FAIL]"
        print(f" {status_symbol} {name}: {detail}")
        if not status:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("All setup checks passed! You are ready to use SyllabusTube.")
    else:
        print("Some checks failed. Please update your environment variables or configuration.")
    print("=" * 60)

    return all_passed


def cli() -> None:
    """CLI entry point parsing arguments and executing actions."""
    parser = argparse.ArgumentParser(
        prog="syllabustube",
        description="Turn your syllabus PDF into a verified, topic-mapped YouTube playlist.",
    )
    parser.add_argument("pdf", nargs="?", help="Path to syllabus PDF file to process.")
    parser.add_argument("--config", default=None, help="Path to custom config.yaml file.")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging."
    )
    parser.add_argument("--ui", action="store_true", help="Launch the web-based user interface.")
    parser.add_argument(
        "--check-setup",
        action="store_true",
        help="Run environment and configuration setup diagnostics.",
    )

    args = parser.parse_args()

    # Configure logging
    setup_logging(verbose=args.verbose)

    if args.ui:
        print("UI not available yet.")
        sys.exit(0)

    if args.check_setup:
        passed = check_setup(config_path=args.config)
        sys.exit(0 if passed else 1)

    if args.pdf:
        # User requested to run on a PDF
        print(f"SyllabusTube: '{args.pdf}' received.")
        print(
            "Notice: The end-to-end pipeline implementation is currently in progress and not implemented yet."
        )
        # Attempt to run pipeline to verify exception handling without traceback
        try:
            cfg = get_config(config_path=args.config)
            pipeline = Pipeline(config=cfg)
            pipeline.run(args.pdf)
        except SyllabusTubeError:
            # Clean exit without traceback as requested
            sys.exit(0)
        except Exception:  # noqa: BLE001
            sys.exit(0)
        sys.exit(0)

    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    cli()
