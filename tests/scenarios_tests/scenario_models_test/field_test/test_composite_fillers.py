import unittest
from unittest.mock import Mock

from core.basic_models.requirement.basic_requirements import Requirement, requirement_factory, TopicRequirement, \
    requirements
from core.model.registered import registered_factories
from scenarios.scenario_models.field.field_filler_description import FieldFillerDescription, field_filler_factory, \
    field_filler_description, FirstNumberFiller, FirstPersonFiller, UserIdFiller
from smart_kit.utils.picklable_mock import PicklableMagicMock

from scenarios.scenario_models.field.composite_fillers import RequirementFiller, ChoiceFiller, ElseFiller


class RequirementFillerTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        registered_factories[FieldFillerDescription] = field_filler_factory
        field_filler_description["number_first"] = FirstNumberFiller
        registered_factories[Requirement] = requirement_factory
        requirements["topic"] = TopicRequirement

    async def test_positive_run(self):
        items = {
            "requirement": {
                "type": "topic",
                "topics": ["test"]
            },
            "filler": {
                "type": "number_first"
            },
        }
        # registered_factories[FieldFillerDescription] = field_filler_factory
        # field_filler_factory["number_first"] = FirstNumberFiller
        filler = RequirementFiller(items)
        text_normalization_result = Mock(num_token_values=[1, 2, 3])
        user = PicklableMagicMock(message=PicklableMagicMock(topic_key="test"))
        params = {}
        result = filler.run(user, text_normalization_result, params)
        self.assertEqual(result, 1)

    async def test_negative_run(self):
        items = {
            "requirement": {
                "type": "topic",
                "topics": ["test"]
            },
            "filler": {
                "type": "number_first"
            },
        }
        filler = RequirementFiller(items)
        text_normalization_result = Mock(num_token_values=[1, 2, 3])
        user = PicklableMagicMock(message=PicklableMagicMock(topic_key="tset"))
        params = {}
        result = filler.run(user, text_normalization_result, params)
        self.assertIsNone(result)


class ChoiceFillerTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        registered_factories[FieldFillerDescription] = field_filler_factory
        field_filler_description["number_first"] = FirstNumberFiller
        field_filler_description["get_first_person"] = FirstPersonFiller
        field_filler_description["user_id"] = UserIdFiller
        registered_factories[Requirement] = requirement_factory
        requirements["topic"] = TopicRequirement

    async def test_first_run(self):
        items = {
            "requirement_fillers": [
                {
                    "requirement": {
                        "type": "topic",
                        "topics": ["test"]
                    },
                    "filler": {
                        "type": "number_first"
                    },
                },
                {
                    "requirement": {
                        "type": "topic",
                        "topics": ["tset"]
                    },
                    "filler": {
                        "type": "get_first_person"
                    },
                }
            ],
            "else_filler": {
                "type": "user_id"
            },
        }
        filler = ChoiceFiller(items)
        text_normalization_result = Mock(num_token_values=[1, 2, 3], person_token_values=["a", "b", "c"])
        user = PicklableMagicMock(message=PicklableMagicMock(topic_key="test", uuid={"userId": "q"}))
        params = {}
        result = filler.run(user, text_normalization_result, params)
        self.assertEqual(result, 1)

    async def test_second_run(self):
        items = {
            "requirement_fillers": [
                {
                    "requirement": {
                        "type": "topic",
                        "topics": ["test"]
                    },
                    "filler": {
                        "type": "number_first"
                    },
                },
                {
                    "requirement": {
                        "type": "topic",
                        "topics": ["tset"]
                    },
                    "filler": {
                        "type": "get_first_person"
                    },
                }
            ],
            "else_filler": {
                "type": "user_id"
            },
        }
        filler = ChoiceFiller(items)
        text_normalization_result = Mock(num_token_values=[1, 2, 3], person_token_values=["a", "b", "c"])
        user = PicklableMagicMock(message=PicklableMagicMock(topic_key="tset", uuid={"userId": "q"}))
        params = {}
        result = filler.run(user, text_normalization_result, params)
        self.assertEqual(result, "a")

    async def test_else_run(self):
        items = {
            "requirement_fillers": [
                {
                    "requirement": {
                        "type": "topic",
                        "topics": ["test"]
                    },
                    "filler": {
                        "type": "number_first"
                    },
                },
                {
                    "requirement": {
                        "type": "topic",
                        "topics": ["tset"]
                    },
                    "filler": {
                        "type": "get_first_person"
                    },
                }
            ],
            "else_filler": {
                "type": "user_id"
            },
        }
        filler = ChoiceFiller(items)
        text_normalization_result = Mock(num_token_values=[1, 2, 3], person_token_values=["a", "b", "c"])
        user = PicklableMagicMock(message=PicklableMagicMock(topic_key="etst", uuid={"userId": "q"}))
        params = {}
        result = filler.run(user, text_normalization_result, params)
        self.assertEqual(result, "q")


class ElseFillerTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        registered_factories[FieldFillerDescription] = field_filler_factory
        field_filler_description["number_first"] = FirstNumberFiller
        field_filler_description["get_first_person"] = FirstPersonFiller
        registered_factories[Requirement] = requirement_factory
        requirements["topic"] = TopicRequirement

    async def test_postitive_run(self):
        items = {
            "requirement": {
                "type": "topic",
                "topics": ["test"]
            },
            "filler": {
                "type": "number_first"
            },
            "else_filler": {
                "type": "get_first_person"
            },
        }
        filler = ElseFiller(items)
        text_normalization_result = Mock(num_token_values=[1, 2, 3], person_token_values=["a", "b", "c"])
        user = PicklableMagicMock(message=PicklableMagicMock(topic_key="test"))
        params = {}
        result = filler.run(user, text_normalization_result, params)
        self.assertEqual(result, 1)

    async def test_else_run(self):
        items = {
            "requirement": {
                "type": "topic",
                "topics": ["test"]
            },
            "filler": {
                "type": "number_first"
            },
            "else_filler": {
                "type": "get_first_person"
            },
        }
        filler = ElseFiller(items)
        text_normalization_result = Mock(num_token_values=[1, 2, 3], person_token_values=["a", "b", "c"])
        user = PicklableMagicMock(message=PicklableMagicMock(topic_key="tset"))
        params = {}
        result = filler.run(user, text_normalization_result, params)
        self.assertEqual(result, "a")
