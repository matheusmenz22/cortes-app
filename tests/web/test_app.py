"""Testes da interface web (TestClient, sem rede: fonte injetada)."""

from fastapi.testclient import TestClient

from cortes_app.sources.base import RawClip
from cortes_app.web.app import create_app

CLIP = RawClip(
    id="AbcSlug",
    url="https://clips.twitch.tv/AbcSlug",
    title="FURIA vs T1",
    creator="CBLOL",
    game="League of Legends",
    duration_s=35.0,
    view_count=1500,
    created_at="2026-07-06T00:19:00Z",
)


class FakeSource:
    def __init__(self, clips: list[RawClip]):
        self._clips = clips
        self.calls: list[tuple[str, int]] = []
        self.langs: list[str] = []

    def top_clips(self, game: str, *, limit: int = 20) -> list[RawClip]:
        self.calls.append((game, limit))
        return self._clips


def _client(clips: list[RawClip], sink: FakeSource | None = None) -> TestClient:
    fake = sink or FakeSource(clips)

    def factory(lang: str) -> FakeSource:
        fake.langs.append(lang)
        return fake

    return TestClient(create_app(source_factory=factory))


def test_index_ok_and_lists_clips():
    r = _client([CLIP]).get("/")
    assert r.status_code == 200
    assert "FURIA vs T1" in r.text
    assert "clips.twitch.tv/embed?clip=AbcSlug" in r.text


def test_index_escapes_html():
    evil = RawClip(
        id="x",
        url="https://clips.twitch.tv/x",
        title="<script>alert(1)</script>",
        creator="c",
        game="g",
        duration_s=1.0,
        view_count=1,
        created_at="t",
    )
    r = _client([evil]).get("/")
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text


def test_index_empty():
    r = _client([]).get("/")
    assert "Nenhum clip" in r.text


def test_index_forwards_query_params():
    sink = FakeSource([])
    _client([], sink=sink).get("/?game=Valorant&limit=5&lang=EN")
    assert sink.calls == [("Valorant", 5)]
    assert sink.langs == ["EN"]
