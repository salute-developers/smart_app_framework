from time import time
from unittest import TestCase

from scenarios.scenario_models.history import Event, History, HistoryEventFormatter
from smart_kit.utils.picklable_mock import PicklableMock


class ScenarioHistoryTest(TestCase):

    def test_event(self):
        item = {
            'scenario': 'name',
            'scenario_version': 'version',
            'node': 'node',
            'results': 'true',
            '_type': '_type',
            'content': {'foo': 'bar'}
        }
        event = Event(**item)

        self.assertEqual(event.scenario, item['scenario'])
        self.assertEqual(event.scenario_version, item['scenario_version'])
        self.assertEqual(event.node, item['node'])
        self.assertEqual(event.results, item['results'])
        self.assertEqual(event.type, item['_type'])
        self.assertDictEqual(event.content, item['content'])

    def test_event_to_dict(self):
        expected = {
            'scenario': 'name',
            'scenario_version': 'version',
            'node': 'node',
            'results': 'true',
            '_type': '_type',
            'content': {'foo': 'bar'},
            'created_time': time()
        }
        event = Event(**expected)

        self.assertDictEqual(event.to_dict(), expected)

    def test_history_add_event(self):
        descriptions = PicklableMock()
        item = {
            '_type': 'event_type',
            'content': {'foo': 'bar'}
        }
        history = History({}, descriptions, None)
        expected = Event(**item)

        history.add_event(expected)

        self.assertEqual(len(history.get_raw_events()), 1)
        self.assertEqual(history.get_raw_events()[0], expected)

    def test_history_clear(self):
        descriptions = PicklableMock()
        items = {
            'events': [
                {
                    '_type': 'event_type_1',
                    'content': {'foo': 'bar'}
                },
                {
                    '_type': 'event_type_2',
                    'content': {'foo': 'bar'}
                }
            ]
        }
        history = History(items, descriptions, None)
        self.assertEqual(len(history.get_raw_events()), 2)

        history.clear()
        self.assertEqual(len(history.get_raw_events()), 0)

    def test_history_raw(self):
        now = time()
        descriptions = PicklableMock()
        items = {
            'events': [
                {
                    '_type': 'event_type_1',
                    'content': {'foo': 'bar'},
                    'created_time': now
                }
            ]
        }
        expected = {
            'events': [
                {
                    '_type': 'event_type_1',
                    'content': {'foo': 'bar'},
                    'node': None,
                    'results': None,
                    'scenario': None,
                    'scenario_version': None,
                    'created_time': now
                }
            ]
        }

        history = History(items, descriptions, None)

        self.assertDictEqual(history.raw, expected)

    def test_history_expire(self):
        now = time()
        descriptions = PicklableMock()
        descriptions.event_expiration_delay = 5
        items = {
            'events': [
                {
                    '_type': 'event_type_1',
                    'content': {'foo': 'bar'},
                    'created_time': now - 1
                },
                {
                    '_type': 'event_type_2',
                    'content': {'foo': 'bar'},
                    'created_time': now - 5
                }
            ]
        }
        expected_keys = {'event_type_1',}

        history = History(items, descriptions, None)
        history.expire()

        history_raw = history.raw
        events_raw = history_raw["events"]
        event_keys = {event_raw.get("_type") for event_raw in events_raw}

        self.assertSetEqual(event_keys, expected_keys)

    def test_history_event_formatter(self):
        events = [
            Event(type='field_event', scenario='name', node='node', results='filled', content={'field': 'foo'}),
            Event(type='field_event', scenario='name', node='node', results='filled', content={'field': 'bar'}),
        ]
        expected = [
            {
                'no': 1,
                'scenarioName': 'name',
                'scenarioVersion': None,
                'results': 'filled',
                'eventType': 'field_event',
                'eventContent': {'field': 'foo'}
            },
            {
                'no': 2,
                'scenarioName': 'name',
                'scenarioVersion': None,
                'results': 'filled',
                'eventType': 'field_event',
                'eventContent': {'field': 'bar'}
            }
        ]

        formatter = HistoryEventFormatter()

        self.assertListEqual(formatter.format(events), expected)

    def test_get_events(self):
        descriptions = PicklableMock()
        descriptions.formatter = HistoryEventFormatter()
        items = {
            'events': [
                {
                    '_type': 'field_event',
                    'scenario': 'name',
                    'node': 'node',
                    'results': 'filled',
                    'content': {'field': 'field_name'}
                }
            ]
        }
        expected = [
            {
                'no': 1,
                'scenarioName': 'name',
                'scenarioVersion': None,
                'results': 'filled',
                'eventType': 'field_event',
                'eventContent': {'field': 'field_name'}
            }
        ]

        history = History(items, descriptions, None)
        events = history.get_events()

        self.assertDictEqual(events[0], expected[0])
