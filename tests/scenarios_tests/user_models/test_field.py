from unittest import TestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.field import QuestionField
from smart_kit.utils.picklable_mock import PicklableMock, PicklableMagicMock


class TestField(TestCase):
    def test_1(self):
        expected = "my_value"
        mock_user = PicklableMock()
        mock_user.settings = {"template_settings": {}}
        description = PicklableMock()
        lifetime = 10
        items = {"value": expected, "available": False}
        field = QuestionField(description, items, mock_user, lifetime)

        result = field.value
        self.assertEqual(expected, result)

    def test_2(self):
        expected = "my_value"
        mock_user = PicklableMock()
        mock_user.settings = {"template_settings": {}}

        description = PicklableMock()
        description.need_load_context = False
        description.default_value = expected

        lifetime = 10
        items = None
        field = QuestionField(description, items, mock_user, lifetime)

        result = field.value
        self.assertEqual(expected, result)

    def test_3(self):
        expected = "prev_value"
        mock_user = PicklableMock()
        mock_user.last_fields = PicklableMagicMock()
        value_mock = PicklableMock()
        value_mock.value = "prev_value"
        mock_user.last_fields.__getitem__.return_value = value_mock
        mock_user.settings = {"template_settings": {}}

        description = PicklableMock()
        description.need_load_context = True
        description.id = 5

        lifetime = 10
        items = None
        field = QuestionField(description, items, mock_user, lifetime)

        result = field.value
        self.assertEqual(expected, result)

    def test_4(self):
        expected = "my_value"
        mock_user = PicklableMock()
        mock_user.last_fields = PicklableMagicMock()
        value_mock = PicklableMock()
        value_mock.value = None
        mock_user.last_fields.__getitem__.return_value = value_mock
        mock_user.settings = {"template_settings": {}}

        description = PicklableMock()
        description.need_load_context = True
        description.id = 5
        description.default_value = expected

        lifetime = 10
        items = None
        field = QuestionField(description, items, mock_user, lifetime)

        result = field.value
        self.assertEqual(expected, result)

    def test_5_1(self):
        mock_user = None
        description = PicklableMock()
        lifetime = 10
        items = {"value": "my_value", "available": True}
        field = QuestionField(description, items, mock_user, lifetime)

        self.assertTrue(field.valid)

    def test_5_2(self):
        mock_user = Mock(last_fields=[])

        description = Mock(default_value=None)
        description.id = 1
        mock_user.last_fields = {description.id: Mock(value=None)}
        mock_user.settings = {"template_settings": {}}

        description.required = False
        lifetime = 10
        items = {"available": True}
        field = QuestionField(description, items, mock_user, lifetime)

        self.assertTrue(field.valid)

    def test_5_3(self):
        mock_user = PicklableMock()

        description = Mock(default_value=None)
        description.id = 1
        mock_user.last_fields = {description.id: Mock(value=None)}
        mock_user.settings = {"template_settings": {}}
        lifetime = 10
        items = {"available": True}
        field = QuestionField(description, items, mock_user, lifetime)

        self.assertFalse(field.valid)

    def test_6_1(self):
        expected = {"value": "my_value", "available": True}

        mock_user = None
        description = PicklableMock()
        description.default_value = "some_value"
        description.available = False
        lifetime = 10
        items = {"value": "my_value", "available": True}
        field = QuestionField(description, items, mock_user, lifetime)

        result = field.raw
        self.assertDictEqual(expected, result)

    def test_6_2(self):
        expected = {"value": "my_value"}

        mock_user = None
        description = PicklableMock()
        description.default_value = "some_value"
        description.available = True
        lifetime = 10
        items = {"value": "my_value", "available": True}
        field = QuestionField(description, items, mock_user, lifetime)

        result = field.raw
        self.assertDictEqual(expected, result)

    def test_6_3(self):
        expected = {}
        mock_user = None
        description = PicklableMock()
        description.default_value = "some_value"
        description.available = True
        lifetime = 10
        items = {"value": None, "available": True}
        field = QuestionField(description, items, mock_user, lifetime)

        result = field.raw
        self.assertEqual(result, expected)

    def test_7_1(self):
        expected = "my_value"
        mock_user = None
        description = PicklableMock()
        description.default_value = "some_value"
        description.available = False
        lifetime = 10
        items = {"value": expected, "available": False}
        field = QuestionField(description, items, mock_user, lifetime)
        field.fill("some_value")
        result = field.value
        self.assertEqual(expected, result)
        self.assertFalse(field.available)

    def test_7_2(self):
        expected = "some_value"
        mock_user = None
        description = PicklableMock()
        description.default_value = "some_value"
        description.available = True
        description.need_save_context = False

        lifetime = 10
        items = {"value": "my_value", "available": True}
        field = QuestionField(description, items, mock_user, lifetime)
        field.fill("some_value")
        result = field.value
        self.assertEqual(expected, result)
        self.assertTrue(field.available)

    def test_7_3(self):
        expected = "some_value"

        mock_value = PicklableMock()
        mock_value.value = None

        mock_user = PicklableMagicMock()
        mock_user.last_fields = PicklableMagicMock()
        mock_user.last_fields.__getitem__.return_value = mock_value

        description = PicklableMock()
        description.id = 5
        description.default_value = expected
        description.available = True
        description.need_save_context = True

        lifetime = 10
        items = {"value": "my_value", "available": True}
        field = QuestionField(description, items, mock_user, lifetime)
        field.fill(expected)
        result = field.value

        self.assertEqual(expected, result)
        self.assertEqual(expected, mock_value.value)

    def test_7_4(self):
        expected = "my_value"
        mock_user = None
        description = PicklableMock()
        description.default_value = "some_value"
        description.available = True
        description.need_save_context = False
        description.need_load_context = False

        lifetime = 10
        items = {"value": "my_value", "available": True}
        field = QuestionField(description, items, mock_user, lifetime)
        field.fill(None)
        result = field.value
        self.assertEqual(expected, result)
        self.assertTrue(field.available)

    def test_set_available(self):
        mock_user = None
        description = PicklableMock()
        description.default_value = "some_value"
        description.available = True
        lifetime = 10
        items = {"value": None, "available": False}
        field = QuestionField(description, items, mock_user, lifetime)
        field.set_available()
        self.assertTrue(field.available)

    def test_set_unavailable(self):
        mock_user = None
        description = PicklableMock()
        description.default_value = "some_value"
        description.available = False
        lifetime = 10
        items = {"value": None, "available": True}
        field = QuestionField(description, items, mock_user, lifetime)
        field.reset_available()
        self.assertFalse(field.available)
