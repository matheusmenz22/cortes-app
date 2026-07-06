"""Interface das fontes de clipes candidatos.

Uma `ClipSource` entrega candidatos brutos (ainda não editados). A 1ª
implementação será a Twitch Clips API (melhores momentos já curados pela
comunidade); depois uma fonte de VOD (detecção própria via chat/áudio/killfeed)
pode ser plugada atrás da MESMA interface, sem mexer no resto do app.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class RawClip:
    """Clipe candidato vindo de uma fonte, antes de qualquer edição."""

    id: str
    url: str
    title: str
    creator: str
    game: str
    duration_s: float
    view_count: int
    created_at: str  # ISO 8601


@runtime_checkable
class ClipSource(Protocol):
    """Fonte de clipes candidatos de um jogo."""

    def top_clips(self, game: str, *, limit: int = 20) -> list[RawClip]:
        """Melhores clipes recentes do jogo, ordenados por relevância (mais
        vistos primeiro)."""
        ...
