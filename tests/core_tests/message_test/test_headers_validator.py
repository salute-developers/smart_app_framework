from unittest import TestCase
from unittest.mock import Mock
import logging
from core.message.from_message import SmartAppFromMessage
from core.message.validators.header_validator import MessageHeadersValidator


class TestHeadersValidator(TestCase):
    def test_valid_true(self):
        message = SmartAppFromMessage({"messageName": "ANSWER_FROM_USER", "messageId": 1111},
                                      headers=[('test_header', b'result')], validators=[MessageHeadersValidator()])
        self.assertTrue(message.validate())

    def test_valid_false(self):
        message = SmartAppFromMessage({"messageName": "ANSWER_FROM_USER", "messageId": 1111},
                                      headers=[], validators=[MessageHeadersValidator()])
        self.assertFalse(message.validate())
