"""TDD do gate de elegibilidade (domínio puro, sem I/O).

Ordem dos filtros (spec `pipeline-shorts.md` §1): duração 8-60s -> blocklist ->
dedup (já visto) -> priority fura fila.
"""

from cortes_app.domain.eligibility import EligibilityRules, eligible_clips
from cortes_app.sources.base import RawClip


def _clip(id: str, *, duration_s: float = 20.0, creator: str = "streamer") -> RawClip:
    return RawClip(
        id=id,
        url=f"https://clips.twitch.tv/{id}",
        title="t",
        creator=creator,
        game="League of Legends",
        duration_s=duration_s,
        view_count=1000,
        created_at="2026-07-06T00:00:00Z",
    )


class TestDuration:
    def test_keeps_clip_inside_window(self):
        clips = [_clip("ok", duration_s=20)]
        assert [c.id for c in eligible_clips(clips, EligibilityRules())] == ["ok"]

    def test_drops_too_short(self):
        clips = [_clip("curto", duration_s=7.9)]
        assert eligible_clips(clips, EligibilityRules()) == []

    def test_drops_too_long(self):
        clips = [_clip("longo", duration_s=60.1)]
        assert eligible_clips(clips, EligibilityRules()) == []

    def test_bounds_are_inclusive(self):
        clips = [_clip("min", duration_s=8), _clip("max", duration_s=60)]
        assert [c.id for c in eligible_clips(clips, EligibilityRules())] == ["min", "max"]


class TestBlocklist:
    def test_drops_blocked_creator(self):
        clips = [_clip("a", creator="banido"), _clip("b", creator="ok")]
        rules = EligibilityRules(blocked_creators=frozenset({"banido"}))
        assert [c.id for c in eligible_clips(clips, rules)] == ["b"]

    def test_blocklist_is_case_insensitive(self):
        clips = [_clip("a", creator="xQc")]
        rules = EligibilityRules(blocked_creators=frozenset({"xqc"}))
        assert eligible_clips(clips, rules) == []


class TestDedup:
    def test_drops_already_seen(self):
        clips = [_clip("velho"), _clip("novo")]
        rules = EligibilityRules(seen_ids=frozenset({"velho"}))
        assert [c.id for c in eligible_clips(clips, rules)] == ["novo"]

    def test_drops_in_batch_duplicates_keeping_first(self):
        clips = [_clip("dup"), _clip("dup"), _clip("outro")]
        assert [c.id for c in eligible_clips(clips, EligibilityRules())] == ["dup", "outro"]


class TestPriority:
    def test_priority_creator_jumps_the_queue(self):
        clips = [_clip("a", creator="comum"), _clip("b", creator="vip")]
        rules = EligibilityRules(priority_creators=frozenset({"vip"}))
        assert [c.id for c in eligible_clips(clips, rules)] == ["b", "a"]

    def test_priority_is_stable_within_each_group(self):
        clips = [
            _clip("a", creator="comum"),
            _clip("b", creator="vip"),
            _clip("c", creator="comum"),
            _clip("d", creator="vip"),
        ]
        rules = EligibilityRules(priority_creators=frozenset({"vip"}))
        assert [c.id for c in eligible_clips(clips, rules)] == ["b", "d", "a", "c"]

    def test_priority_match_is_case_insensitive(self):
        clips = [_clip("a", creator="comum"), _clip("b", creator="Loud")]
        rules = EligibilityRules(priority_creators=frozenset({"loud"}))
        assert [c.id for c in eligible_clips(clips, rules)] == ["b", "a"]


class TestOrderOfGates:
    def test_ineligible_priority_clip_is_still_dropped(self):
        # priority não fura os filtros de duração/blocklist/dedup — só reordena
        clips = [_clip("curto", duration_s=5, creator="vip"), _clip("ok", creator="comum")]
        rules = EligibilityRules(priority_creators=frozenset({"vip"}))
        assert [c.id for c in eligible_clips(clips, rules)] == ["ok"]

    def test_empty_input(self):
        assert eligible_clips([], EligibilityRules()) == []
