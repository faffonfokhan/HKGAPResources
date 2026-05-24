from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from rich import print

from .agents.base import build_provider
from .agents.editor_in_chief import EditorInChiefAgent
from .config import Settings
from .pdf_loader import extract_paragraphs
from .renderer import render_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hkgap_review")
    subparsers = parser.add_subparsers(dest="command", required=True)

    review_parser = subparsers.add_parser("review", help="Review a paper PDF")
    review_parser.add_argument("--pdf", required=True, type=Path, help="Path to source PDF")
    review_parser.add_argument("--out", required=True, type=Path, help="Output markdown path")
    review_parser.add_argument(
        "--provider",
        choices=["openai", "azure_openai", "anthropic", "mock"],
        default=None,
        help="LLM provider selector",
    )
    review_parser.add_argument("--model", default=None, help="Override model name")
    return parser


async def _run_review(
    pdf_path: Path, out_path: Path, provider: str | None, model: str | None
) -> int:
    load_dotenv()
    settings = Settings.from_env(provider_override=provider, model_override=model)
    paragraphs = extract_paragraphs(pdf_path)

    llm = build_provider(settings)
    editor = EditorInChiefAgent(llm, settings)
    report = await editor.review_document(paragraphs)

    markdown = render_report(report)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")

    print(f"[green]Wrote review:[/green] {out_path}")
    print(f"[green]Paragraphs reviewed:[/green] {len(paragraphs)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "review":
        return asyncio.run(_run_review(args.pdf, args.out, args.provider, args.model))

    parser.error("Unsupported command")
    return 2
