from unittest import TestCase

from core.utils.stats_timer import StatsTimer


class TestStatsTimer(TestCase):

    def test_1(self):
        timer = StatsTimer()
        with timer:
            _ = 3

        self.assertTrue(timer.msecs > 0)
