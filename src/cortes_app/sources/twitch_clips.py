"""Discovery de clipes via GQL público da Twitch — sem credencial.

Os melhores momentos já vêm curados pela comunidade (clips mais vistos). O
transporte HTTP (`post`) é injetado para testabilidade: os testes usam um fake
e não tocam a rede; em produção use `httpx_transport()`.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from cortes_app.sources.base import RawClip

GQL_URL = "https://gql.twitch.tv/gql"
# Client-Id PÚBLICO do site da Twitch (vem no JS do site; NÃO é segredo).
WEB_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"

# transporte: recebe (query, variables) e devolve o JSON já parseado
GqlPost = Callable[[str, dict[str, Any]], dict[str, Any]]

_CLIP_BASE_URL = "https://clips.twitch.tv/"
_LANGUAGE = re.compile(r"^[A-Z]{2}$")

# `game` e `first` como variáveis; `languages` interpolado (validado) porque é
# um enum GQL (não aceita variável String sem tipar o enum).
_QUERY = """\
query TopClips($game: String!, $first: Int!) {{
  game(name: $game) {{
    clips(first: $first, criteria: {{period: LAST_DAY, sort: VIEWS_DESC, languages: [{lang}]}}) {{
      edges {{ node {{
        slug title viewCount durationSeconds createdAt
        broadcaster {{ displayName }}
      }} }}
    }}
  }}
}}"""


@dataclass
class TwitchClipsSource:
    """`ClipSource` que lista os clipes mais vistos de um jogo na Twitch."""

    post: GqlPost
    language: str = "PT"

    def __post_init__(self) -> None:
        if not _LANGUAGE.match(self.language):
            raise ValueError(f"idioma inválido: {self.language!r} (use 2 letras, ex.: 'PT')")

    def top_clips(self, game: str, *, limit: int = 20) -> list[RawClip]:
        if limit <= 0:
            raise ValueError("limit deve ser > 0")
        query = _QUERY.format(lang=self.language)
        data = self.post(query, {"game": game, "first": limit})

        if data.get("errors"):
            msgs = "; ".join(e.get("message", "?") for e in data["errors"])
            raise RuntimeError(f"GQL da Twitch retornou erro: {msgs}")

        game_node = (data.get("data") or {}).get("game")
        if not game_node:  # jogo inexistente / sem dados
            return []
        edges = (game_node.get("clips") or {}).get("edges") or []
        return [_to_rawclip(edge["node"], game) for edge in edges]


def _to_rawclip(node: dict[str, Any], game: str) -> RawClip:
    slug = node["slug"]
    return RawClip(
        id=slug,
        url=f"{_CLIP_BASE_URL}{slug}",
        title=node["title"],
        creator=node["broadcaster"]["displayName"],
        game=game,
        duration_s=float(node["durationSeconds"]),
        view_count=int(node["viewCount"]),
        created_at=node["createdAt"],
    )


def httpx_transport(client_id: str = WEB_CLIENT_ID, timeout: float = 20.0) -> GqlPost:
    """Transporte de produção (httpx). Import local p/ não exigir httpx nos testes."""
    import httpx

    def post(query: str, variables: dict[str, Any]) -> dict[str, Any]:
        resp = httpx.post(
            GQL_URL,
            headers={"Client-Id": client_id},
            json={"query": query, "variables": variables},
            timeout=timeout,
        )
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result

    return post
