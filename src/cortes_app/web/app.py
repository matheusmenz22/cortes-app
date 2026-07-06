"""App web (FastAPI): lista os clips descobertos com player embutido da Twitch.

Consome uma `ClipSource` (injetável para testes). A página é montada no servidor
— sem framework de front. Rode com: `python -m cortes_app.web`.
"""

from __future__ import annotations

import html
from collections.abc import Callable

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from cortes_app.sources.base import ClipSource, RawClip
from cortes_app.sources.twitch_clips import TwitchClipsSource, httpx_transport

SourceFactory = Callable[[str], ClipSource]

_STYLE = """
* { box-sizing: border-box; }
body { margin: 0; font: 15px/1.5 system-ui, sans-serif; background: #0e0e10; color: #efeff1; }
header { padding: 24px; border-bottom: 1px solid #2a2a2d; }
header h1 { margin: 0 0 4px; font-size: 22px; }
header p { margin: 0; color: #adadb8; }
.grid { display: grid; gap: 18px; padding: 24px;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); }
.card { background: #18181b; border: 1px solid #2a2a2d; border-radius: 10px; overflow: hidden; }
.player { position: relative; aspect-ratio: 16/9; background: #000; }
.player iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
.meta { padding: 12px 14px; }
.meta h3 { margin: 0 0 6px; font-size: 15px; line-height: 1.3; }
.meta p { margin: 0 0 8px; color: #adadb8; font-size: 13px; }
.meta a { color: #a970ff; text-decoration: none; font-size: 13px; }
.meta a:hover { text-decoration: underline; }
.empty { padding: 40px 24px; color: #adadb8; }
"""


def _twitch_source(language: str) -> ClipSource:
    return TwitchClipsSource(post=httpx_transport(), language=language)


def _clip_card(c: RawClip) -> str:
    slug = html.escape(c.id, quote=True)
    embed = (
        f"https://clips.twitch.tv/embed?clip={slug}"
        "&parent=localhost&parent=127.0.0.1&autoplay=false"
    )
    return (
        '<article class="card">'
        f'<div class="player"><iframe src="{embed}" allowfullscreen loading="lazy"></iframe></div>'
        '<div class="meta">'
        f"<h3>{html.escape(c.title)}</h3>"
        f"<p>{html.escape(c.creator)} · {c.view_count} views · {c.duration_s:.0f}s</p>"
        f'<a href="{html.escape(c.url, quote=True)}" target="_blank" rel="noopener">'
        "abrir na Twitch ↗</a>"
        "</div></article>"
    )


def _render(clips: list[RawClip], game: str) -> str:
    if clips:
        body = '<main class="grid">' + "\n".join(_clip_card(c) for c in clips) + "</main>"
    else:
        body = '<p class="empty">Nenhum clip encontrado.</p>'
    game_safe = html.escape(game)
    return (
        "<!doctype html><html lang='pt-br'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>cortes-app · {game_safe}</title><style>{_STYLE}</style></head><body>"
        f"<header><h1>🎬 cortes-app</h1><p>Top clips de <b>{game_safe}</b> "
        "nas últimas 24h (Twitch, PT)</p></header>"
        f"{body}</body></html>"
    )


def create_app(source_factory: SourceFactory = _twitch_source) -> FastAPI:
    app = FastAPI(title="cortes-app")

    @app.get("/", response_class=HTMLResponse)
    def index(
        game: str = Query("League of Legends"),
        lang: str = Query("PT"),
        limit: int = Query(12, ge=1, le=100),
    ) -> str:
        clips = source_factory(lang).top_clips(game, limit=limit)
        return _render(clips, game)

    return app


app = create_app()
