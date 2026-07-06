"""Testes da CLI (sem rede: injeta uma fonte falsa)."""

from cortes_app import __main__ as cli
from cortes_app.sources.base import RawClip

CLIP = RawClip(
    id="s",
    url="https://clips.twitch.tv/s",
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

    def top_clips(self, game: str, *, limit: int = 20) -> list[RawClip]:
        self.calls.append((game, limit))
        return self._clips


def test_discover_prints_clips(capsys):
    rc = cli.main(
        ["discover", "League of Legends", "--limit", "5"],
        source_factory=lambda _lang: FakeSource([CLIP]),
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "FURIA vs T1" in out
    assert "https://clips.twitch.tv/s" in out


def test_discover_forwards_args():
    fake = FakeSource([])
    seen: dict[str, str] = {}

    def factory(lang: str):
        seen["lang"] = lang
        return fake

    cli.main(["discover", "LoL", "--limit", "3", "--lang", "EN"], source_factory=factory)
    assert seen["lang"] == "EN"
    assert fake.calls == [("LoL", 3)]


def test_discover_empty(capsys):
    cli.main(["discover", "X"], source_factory=lambda _lang: FakeSource([]))
    assert "nenhum clip" in capsys.readouterr().out


def test_discover_handles_emoji_title(capsys):
    """Título com emoji não pode derrubar a CLI (Windows/cp1252)."""
    clip = RawClip(
        id="e",
        url="https://clips.twitch.tv/e",
        title="GG‼ pentakill 🔥",
        creator="x",
        game="LoL",
        duration_s=10.0,
        view_count=5,
        created_at="2026-07-06T00:00:00Z",
    )
    rc = cli.main(["discover", "LoL"], source_factory=lambda _lang: FakeSource([clip]))
    assert rc == 0
    assert "pentakill" in capsys.readouterr().out
