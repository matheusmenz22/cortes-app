"""TDD do adapter de discovery da Twitch (GQL público, sem credencial).

Os testes injetam um transporte falso — nenhuma chamada de rede é feita aqui.
"""

import pytest

from cortes_app.sources.base import ClipSource, RawClip
from cortes_app.sources.twitch_clips import TwitchClipsSource


class FakeTransport:
    """Captura (query, variables) e devolve uma resposta GQL canned."""

    def __init__(self, response: dict):
        self.response = response
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, query: str, variables: dict) -> dict:
        self.calls.append((query, variables))
        return self.response


def _gql(*nodes: dict) -> dict:
    return {"data": {"game": {"clips": {"edges": [{"node": n} for n in nodes]}}}}


NODE = {
    "slug": "AbcSlug-123",
    "title": "FURIA vs T1",
    "viewCount": 1500,
    "durationSeconds": 35,
    "createdAt": "2026-07-06T00:19:00Z",
    "broadcaster": {"displayName": "CBLOL"},
}


class TestContract:
    def test_satisfies_clipsource_protocol(self):
        src = TwitchClipsSource(post=FakeTransport(_gql()))
        assert isinstance(src, ClipSource)


class TestMapping:
    def test_maps_node_to_rawclip(self):
        src = TwitchClipsSource(post=FakeTransport(_gql(NODE)))
        clips = src.top_clips("League of Legends")
        assert clips == [
            RawClip(
                id="AbcSlug-123",
                url="https://clips.twitch.tv/AbcSlug-123",
                title="FURIA vs T1",
                creator="CBLOL",
                game="League of Legends",
                duration_s=35.0,
                view_count=1500,
                created_at="2026-07-06T00:19:00Z",
            )
        ]

    def test_preserves_order(self):
        a = {**NODE, "slug": "a", "viewCount": 900}
        b = {**NODE, "slug": "b", "viewCount": 100}
        src = TwitchClipsSource(post=FakeTransport(_gql(a, b)))
        assert [c.id for c in src.top_clips("LoL")] == ["a", "b"]


class TestQuery:
    def test_passes_limit_and_game_as_variables(self):
        t = FakeTransport(_gql())
        TwitchClipsSource(post=t).top_clips("League of Legends", limit=7)
        _query, variables = t.calls[0]
        assert variables == {"game": "League of Legends", "first": 7}

    def test_query_filters_by_language(self):
        t = FakeTransport(_gql())
        TwitchClipsSource(post=t, language="PT").top_clips("LoL")
        query, _vars = t.calls[0]
        assert "languages: [PT]" in query
        assert "VIEWS_DESC" in query

    def test_invalid_language_rejected(self):
        with pytest.raises(ValueError):
            TwitchClipsSource(post=FakeTransport(_gql()), language="portugues")


class TestEdgeCases:
    def test_game_not_found_returns_empty(self):
        src = TwitchClipsSource(post=FakeTransport({"data": {"game": None}}))
        assert src.top_clips("Jogo Inexistente") == []

    def test_no_edges_returns_empty(self):
        src = TwitchClipsSource(post=FakeTransport(_gql()))
        assert src.top_clips("LoL") == []

    def test_gql_errors_raise(self):
        resp = {"errors": [{"message": "boom"}]}
        src = TwitchClipsSource(post=FakeTransport(resp))
        with pytest.raises(RuntimeError, match="boom"):
            src.top_clips("LoL")

    def test_limit_must_be_positive(self):
        src = TwitchClipsSource(post=FakeTransport(_gql()))
        with pytest.raises(ValueError):
            src.top_clips("LoL", limit=0)
