from unittest import TestCase

from scenarios.utils.make_json_serializable import make_serializable


class TestMakeJsonSerializable(TestCase):
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
