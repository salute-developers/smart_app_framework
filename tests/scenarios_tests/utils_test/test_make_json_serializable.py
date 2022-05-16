from unittest import TestCase

from scenarios.utils.make_json_serializable import make_serializable


class TestMakeJsonSerializable(TestCase):

    def setUp(self):
        self.forms_dict = {'pay_phone_scenario':
                               {'fields': {'amount': {'value': 100.0}, 'approve': {'available': True, 'value': True}},
                                'remove_time': 1506418333}, 'callcenter_scenario': {'remove_time': 2506421370}}

    def serialize_unserializable(self):
        def foo():
            return "bar"

        expected = {"key": str(foo), "serializable": {"hello": "yes", "num": 2, "list": ["0", 1], "tuple": (1, 2),
                                                      "set": {0, 2}}}

        unserializable = {"key": foo,
                          "serializable": {"hello": "yes", "num": 2, "list": ["0", 1], "tuple": (1, 2), "set": {0, 2}}}
        serialized = make_serializable(unserializable)
        self.assertEqual(serialized, expected)

    def serialize_serializable(self):
        expected = {"key": "bar", "serializable": {"hello": "yes", "num": 2, "list": ["0", 1], "tuple": (1, 2),
                                                   "set": {0, 2}}}

        serializable = {"key": "bar",
                        "serializable": {"hello": "yes", "num": 2, "list": ["0", 1], "tuple": (1, 2), "set": {0, 2}}}
        serialized = make_serializable(serializable)
        self.assertEqual(serialized, expected)
