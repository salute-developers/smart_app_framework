# coding: utf-8
import asyncio
import time
import unittest
from unittest.mock import Mock

from core.basic_models.variables.variables import Variables
from core.utils.stats_timer import StatsTimer


class StatsTimerTest(unittest.IsolatedAsyncioTestCase):
    def test_no_inner_stats(self):
        user = Mock()
        user.variables = Variables(None, None)
        user.message = Mock(incremental_id=123)
        with StatsTimer(user=user):
            time.sleep(0.1)
        self.assertIsNone(user.variables.get(key="123script_time_ms"))
        self.assertIsNone(user.variables.get(key="123inner_stats"))

    def test_single_inner_stats(self):
        user = Mock()
        user.variables = Variables(None, None)
        user.message = Mock(incremental_id=123)
        user.variables.set(key="123script_time_ms", value=1000)
        with StatsTimer(add_to_inner_stats=True, user=user):
            time.sleep(0.1)
        self.assertAlmostEqual(first=user.variables.get(key="123script_time_ms"), second=900, places=-2)
        self.assertIsNone(user.variables.get(key="123inner_stats")[0]["system"])
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["inner_stats"], second=[])
        self.assertAlmostEqual(first=user.variables.get(key="123inner_stats")[0]["time"], second=100, places=-2)
        self.assertIsNone(user.variables.get(key="123inner_stats")[0]["version"])
        self.assertEqual(first=len(user.variables.get(key="123inner_stats")), second=1)
        self.assertEqual(first=len(user.variables.get(key="123inner_stats")[0]), second=4)

    def test_consequent_inner_stats(self):
        user = Mock()
        user.variables = Variables(None, None)
        user.message = Mock(incremental_id=123)
        with StatsTimer(add_to_inner_stats=True, user=user, system="test_sys"):
            time.sleep(0.1)
        user.variables.get(key="123inner_stats")[-1]["version"] = "1337"
        with StatsTimer(add_to_inner_stats=True, user=user):
            time.sleep(0.1)
        self.assertAlmostEqual(first=user.variables.get(key="123script_time_ms"), second=-200, places=-2)
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["system"], second="test_sys")
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["inner_stats"], second=[])
        self.assertAlmostEqual(first=user.variables.get(key="123inner_stats")[0]["time"], second=100, places=-2)
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["version"], second="1337")
        self.assertIsNone(user.variables.get(key="123inner_stats")[1]["system"])
        self.assertEqual(first=user.variables.get(key="123inner_stats")[1]["inner_stats"], second=[])
        self.assertAlmostEqual(first=user.variables.get(key="123inner_stats")[1]["time"], second=100, places=-2)
        self.assertIsNone(user.variables.get(key="123inner_stats")[1]["version"])
        self.assertEqual(first=len(user.variables.get(key="123inner_stats")), second=2)
        self.assertEqual(first=len(user.variables.get(key="123inner_stats")[0]), second=4)
        self.assertEqual(first=len(user.variables.get(key="123inner_stats")[1]), second=4)

    def test_nested_inner_stats(self):
        user = Mock()
        user.variables = Variables(None, None)
        user.message = Mock(incremental_id=123)
        with StatsTimer(add_to_inner_stats=True, user=user, system="test_sys"):
            with StatsTimer(add_to_inner_stats=True, user=user, system="inner_sys"):
                time.sleep(0.1)
            user.variables.get(key="123inner_stats")[-1]["version"] = "123"
            time.sleep(0.1)
        user.variables.get(key="123inner_stats")[-1]["version"] = "1337"
        self.assertAlmostEqual(first=user.variables.get(key="123script_time_ms"), second=-200, places=-2)
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["system"], second="inner_sys")
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["inner_stats"], second=[])
        self.assertAlmostEqual(first=user.variables.get(key="123inner_stats")[0]["time"], second=100, places=-2)
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["version"], second="123")
        self.assertEqual(first=user.variables.get(key="123inner_stats")[1]["system"], second="test_sys")
        self.assertEqual(first=user.variables.get(key="123inner_stats")[1]["inner_stats"], second=[])
        self.assertAlmostEqual(first=user.variables.get(key="123inner_stats")[1]["time"], second=100, places=-2)
        self.assertEqual(first=user.variables.get(key="123inner_stats")[1]["version"], second="1337")
        self.assertEqual(first=len(user.variables.get(key="123inner_stats")), second=2)

    async def test_overlapping_inner_stats(self):
        user = Mock()
        user.variables = Variables(None, None)
        user.message = Mock(incremental_id=123)

        async def coro(num: int, duration: float, version: str):
            with StatsTimer(add_to_inner_stats=True, user=user, system=f"test_sys{num}"):
                await asyncio.sleep(duration)
            user.variables.get(key="123inner_stats")[-1]["version"] = version

        first = asyncio.create_task(coro(num=1, duration=0.1, version="1337"))
        second = asyncio.create_task(coro(num=2, duration=0.2, version="123"))
        await first
        await second
        self.assertAlmostEqual(first=user.variables.get(key="123script_time_ms"), second=-200, places=-2)
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["system"], second="test_sys1")
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["inner_stats"], second=[])
        self.assertAlmostEqual(first=user.variables.get(key="123inner_stats")[0]["time"], second=100, places=-2)
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["version"], second="1337")
        self.assertEqual(first=user.variables.get(key="123inner_stats")[1]["system"], second="test_sys2")
        self.assertEqual(first=user.variables.get(key="123inner_stats")[1]["inner_stats"], second=[])
        self.assertAlmostEqual(first=user.variables.get(key="123inner_stats")[1]["time"], second=100, places=-2)
        self.assertEqual(first=user.variables.get(key="123inner_stats")[1]["version"], second="123")

    def test_custom_inner_inner_stats(self):
        user = Mock()
        user.variables = Variables(None, None)
        user.message = Mock(incremental_id=123)
        user.variables.set(key="123script_time_ms", value=1000)
        with StatsTimer(add_to_inner_stats=True, user=user):
            time.sleep(0.1)
        user.variables.get(key="123inner_stats")[-1]["inner_stats"].append({
            "system": "custom",
            "inner_stats": [],
            "time": 100,
            "version": "C-01.001.00",
        })
        self.assertAlmostEqual(first=user.variables.get(key="123script_time_ms"), second=900, places=-2)
        self.assertIsNone(user.variables.get(key="123inner_stats")[0]["system"])
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["inner_stats"][0]["system"], second="custom")
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["inner_stats"][0]["inner_stats"], second=[])
        self.assertAlmostEqual(first=user.variables.get(key="123inner_stats")[0]["inner_stats"][0]["time"], second=100, places=-2)
        self.assertEqual(first=user.variables.get(key="123inner_stats")[0]["inner_stats"][0]["version"], second="C-01.001.00")
        self.assertAlmostEqual(first=user.variables.get(key="123inner_stats")[0]["time"], second=100, places=-2)
        self.assertIsNone(user.variables.get(key="123inner_stats")[0]["version"])
