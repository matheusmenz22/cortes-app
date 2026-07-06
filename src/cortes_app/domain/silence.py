"""Corte de vácuos: detecção pura dos intervalos de FALA a manter num clipe.

Dado o alinhamento por palavra (start/end em segundos da fonte), calcula quais
trechos manter dentro de [clip_start, clip_end], removendo as pausas sem fala
maiores que `min_gap` (com folga `pad` nas bordas p/ não comer início/fim da
fala). É a base do corte fluido de silêncios que melhora a retenção nos Shorts.

Puro: sem ffmpeg, sem I/O — 100% testável. A camada de edição consome os
intervalos e faz o corte/dissolve real do vídeo+áudio.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import pairwise

# timestamps de vídeo em precisão de milissegundo (evita ruído de float)
_MS = 3
# tolerâncias (s): fragmentos menores que isto não valem um corte/segmento
_MIN_SEGMENT = 0.05
_MIN_STEP = 0.02


@dataclass(frozen=True)
class Word:
    """Palavra alinhada no tempo da fonte (segundos)."""

    start: float
    end: float
    text: str = ""


@dataclass(frozen=True)
class Interval:
    """Trecho a MANTER, na timeline do clipe (t=0 == clip_start)."""

    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


def keep_intervals(
    words: Iterable[Word],
    clip_start: float,
    clip_end: float,
    *,
    min_gap: float = 0.4,
    pad: float = 0.1,
) -> list[Interval]:
    """Intervalos de fala a manter em [clip_start, clip_end].

    - Sem pausas qualificadas (ou < 2 palavras): devolve o clipe inteiro.
    - Duração <= 0: devolve lista vazia.

    Args:
        min_gap: remove pausas MAIORES que isto (segundos).
        pad: folga mantida nas bordas de cada pausa removida (segundos).
    """
    if min_gap < 0 or pad < 0:
        raise ValueError("min_gap e pad devem ser >= 0")

    duration = round(clip_end - clip_start, _MS)
    if duration <= 0:
        return []
    full = [Interval(0.0, duration)]

    inside = sorted(
        (w for w in words if clip_start - 0.05 <= w.start <= clip_end + 0.05),
        key=lambda w: w.start,
    )
    if len(inside) < 2:
        return full

    # pausas a REMOVER (na timeline do clipe), já com a folga aplicada
    removed: list[tuple[float, float]] = []
    for a, b in pairwise(inside):
        if b.start - a.end > min_gap:
            gap_start = (a.end - clip_start) + pad
            gap_end = (b.start - clip_start) - pad
            if gap_end - gap_start > _MIN_SEGMENT:
                removed.append((max(0.0, gap_start), min(duration, gap_end)))
    if not removed:
        return full

    # MANTER = [0, duration] menos as pausas removidas
    keep: list[Interval] = []
    cursor = 0.0
    for gap_start, gap_end in removed:
        if gap_start > cursor + _MIN_STEP:
            keep.append(Interval(round(cursor, _MS), round(gap_start, _MS)))
        cursor = max(cursor, gap_end)
    if cursor < duration - _MIN_STEP:
        keep.append(Interval(round(cursor, _MS), duration))

    return [iv for iv in keep if iv.duration > _MIN_SEGMENT]
