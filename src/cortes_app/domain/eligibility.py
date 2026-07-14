"""Gate de elegibilidade: filtra clips brutos ANTES de baixar/renderizar.

Domínio puro (sem I/O): recebe os clips e o estado (blocklist, já-vistos,
prioridade) e devolve a fila elegível já ordenada. A ordem dos filtros é o ouro
do pipeline (spec `pipeline-shorts.md` §1):

    duração 8-60s -> blocklist -> dedup (já visto) -> priority fura fila

`priority` só REORDENA (streamer VIP na frente da fila); nunca fura os filtros
anteriores — um clip inelegível continua fora mesmo sendo de streamer VIP.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from cortes_app.sources.base import RawClip

MIN_DURATION_S = 8.0
MAX_DURATION_S = 60.0


@dataclass(frozen=True)
class EligibilityRules:
    """Estado que decide a elegibilidade. Nomes casefolded na comparação."""

    blocked_creators: frozenset[str] = field(default_factory=frozenset)
    seen_ids: frozenset[str] = field(default_factory=frozenset)
    priority_creators: frozenset[str] = field(default_factory=frozenset)
    min_duration_s: float = MIN_DURATION_S
    max_duration_s: float = MAX_DURATION_S


def eligible_clips(clips: Iterable[RawClip], rules: EligibilityRules) -> list[RawClip]:
    """Fila elegível: filtra (duração → blocklist → dedup) e reordena (priority)."""
    blocked = {c.casefold() for c in rules.blocked_creators}
    priority = {c.casefold() for c in rules.priority_creators}

    passed: list[RawClip] = []
    batch_seen: set[str] = set()
    for clip in clips:
        if not rules.min_duration_s <= clip.duration_s <= rules.max_duration_s:
            continue
        if clip.creator.casefold() in blocked:
            continue
        if clip.id in rules.seen_ids or clip.id in batch_seen:
            continue
        batch_seen.add(clip.id)
        passed.append(clip)

    # priority fura fila: partição estável (mantém a ordem original em cada grupo)
    head = [c for c in passed if c.creator.casefold() in priority]
    tail = [c for c in passed if c.creator.casefold() not in priority]
    return head + tail
