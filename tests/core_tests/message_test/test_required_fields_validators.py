from unittest import TestCase
from unittest.mock import Mock
import logging
from core.message.from_message import SmartAppFromMessage
from core.message.validators.required_fields_validator import RequiredFieldsValidator

validator = RequiredFieldsValidator({
    None: ('1', '2'),
    "MESSAGE": ('1', '2', '3'),
})

validator_types = RequiredFieldsValidator({
    None: ('1', '2'),
    "MESSAGE": ('1', '2', '3'),
}, {'1': int, '2': str})

msg = {
    "messageName": "OOO",
    "1": "test",
    "2": ["test1", "test2"]
}

class TestRequiredFieldsValidator(TestCase):
    def test_valid_true(self):
        message = SmartAppFromMessage({
            "messageName": "OOO",
            "1": "test",
            "2": ["test1", "test2"]
        }, headers=[('test_header', b'result')], validators=[validator])
        self.assertTrue(message.validate())

        message2 = SmartAppFromMessage({
            "messageName": "MESSAGE",
            "1": "test",
            "2": ["test1", "test2"],
            "3": {},
        }, headers=[('test_header', b'result')], validators=[validator])
        self.assertTrue(message2.validate())

    def test_valid_types_true(self):
        message = SmartAppFromMessage({
            "messageName": "OOO",
            "1": 123,
            "2": "str"
        }, headers=[('test_header', b'result')], validators=[validator_types])
        self.assertTrue(message.validate())

    def test_valid_false(self):
        message = SmartAppFromMessage({
            "messageName": "OOO",
            "10": "test",
            "2": ["test1", "test2"]
        }, headers=[('test_header', b'result')], validators=[validator])
        self.assertFalse(message.validate())

        message2 = SmartAppFromMessage({
            "messageName": "MESSAGE",
            "1": "test",
            "2": ["test1", "test2"],
        }, headers=[('test_header', b'result')], validators=[validator])
        self.assertFalse(message2.validate())

    def test_valid_types_false(self):
        message = SmartAppFromMessage({
            "messageName": "OOO",
            "1": {},
            "2": []
        }, headers=[('test_header', b'result')], validators=[validator_types])
        self.assertFalse(message.validate())
