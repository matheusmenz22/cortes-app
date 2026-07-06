"""TDD do domínio de corte de vácuos (puro, sem ffmpeg)."""

import pytest

from cortes_app.domain.silence import Interval, Word, keep_intervals


def w(start: float, end: float) -> Word:
    return Word(start=start, end=end, text="x")


class TestInterval:
    def test_duration(self):
        assert Interval(1.0, 3.5).duration == pytest.approx(2.5)


class TestKeepIntervals:
    def test_removes_long_gap(self):
        words = [
            w(0.0, 0.5),
            w(0.5, 1.0),  # bloco de fala 1
            w(3.0, 3.5),
            w(3.5, 4.0),  # bloco 2 (pausa 1.0->3.0 = 2s)
            w(4.3, 5.0),
        ]  # pausa 4.0->4.3 = 0.3s (curta, fica)
        keep = keep_intervals(words, 0.0, 5.0, min_gap=0.6, pad=0.15)
        assert keep == [Interval(0.0, 1.15), Interval(2.85, 5.0)]

    def test_no_gap_returns_full_clip(self):
        words = [w(0.0, 0.5), w(0.5, 1.0), w(1.0, 1.5)]
        assert keep_intervals(words, 0.0, 2.0) == [Interval(0.0, 2.0)]

    def test_too_few_words_returns_full_clip(self):
        assert keep_intervals([w(0.0, 1.0)], 0.0, 2.0) == [Interval(0.0, 2.0)]
        assert keep_intervals([], 0.0, 2.0) == [Interval(0.0, 2.0)]

    def test_zero_duration_returns_empty(self):
        assert keep_intervals([w(0, 1)], 5.0, 5.0) == []

    def test_ignores_words_outside_window(self):
        words = [w(-2.0, -1.0), w(0.0, 0.5), w(0.5, 1.0), w(3.0, 3.5), w(9.0, 9.5)]
        keep = keep_intervals(words, 0.0, 4.0, min_gap=0.6, pad=0.15)
        assert keep[0].start == 0.0
        assert len(keep) == 2

    def test_multiple_gaps(self):
        words = [w(0.0, 0.5), w(2.0, 2.5), w(4.0, 4.5)]
        keep = keep_intervals(words, 0.0, 5.0, min_gap=0.6, pad=0.1)
        assert len(keep) == 3

    def test_kept_total_shorter_than_full_when_cutting(self):
        words = [w(0.0, 0.5), w(0.5, 1.0), w(3.0, 3.5), w(3.5, 4.0)]
        keep = keep_intervals(words, 0.0, 4.0, min_gap=0.6, pad=0.15)
        total = sum(iv.duration for iv in keep)
        assert total < 4.0

    def test_unsorted_input_is_handled(self):
        words = [w(3.5, 4.0), w(0.0, 0.5), w(3.0, 3.5), w(0.5, 1.0)]
        keep = keep_intervals(words, 0.0, 4.0, min_gap=0.6, pad=0.15)
        assert keep == [Interval(0.0, 1.15), Interval(2.85, 4.0)]

    def test_negative_min_gap_rejected(self):
        with pytest.raises(ValueError):
            keep_intervals([w(0, 1)], 0.0, 2.0, min_gap=-1)
