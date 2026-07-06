"""Interface de linha de comando do cortes-app.

Uso:
    python -m cortes_app discover "League of Legends" --limit 10 --lang PT
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence

from cortes_app.sources.base import ClipSource
from cortes_app.sources.twitch_clips import TwitchClipsSource, httpx_transport

SourceFactory = Callable[[str], ClipSource]


def _twitch_source(language: str) -> ClipSource:
    return TwitchClipsSource(post=httpx_transport(), language=language)


def _force_utf8_output() -> None:
    """No Windows o console padrão é cp1252 e quebra em emoji/acento dos títulos
    da Twitch. Reconfigura stdout/stderr p/ UTF-8 (no-op se já for/não suportar)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(
    argv: Sequence[str] | None = None,
    *,
    source_factory: SourceFactory = _twitch_source,
) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(
        prog="cortes-app", description="Gerador de cortes verticais a partir da Twitch."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    disc = sub.add_parser("discover", help="lista os clips mais vistos de um jogo")
    disc.add_argument("game", help='nome do jogo (ex.: "League of Legends")')
    disc.add_argument("--limit", type=int, default=10, help="quantos clips (padrão: 10)")
    disc.add_argument("--lang", default="PT", help="idioma dos clips (padrão: PT)")

    args = parser.parse_args(argv)

    if args.command == "discover":
        source = source_factory(args.lang)
        clips = source.top_clips(args.game, limit=args.limit)
        for c in clips:
            print(f"{c.view_count:>6} views | {c.duration_s:>4.0f}s | {c.creator} | {c.title}")
            print(f"         {c.url}")
        if not clips:
            print("(nenhum clip encontrado)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
