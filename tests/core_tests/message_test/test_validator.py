from unittest import TestCase
from unittest.mock import Mock
import logging
from core.message.from_message import SmartAppFromMessage
from core.message.validators.base_validator import BaseMessageValidator, ValidationException


class MockMessageValidator(BaseMessageValidator):

    def _validate(self, message: SmartAppFromMessage):
        if not message.message_name == "test":
            raise ValidationException("message_name is not test")


class TestValidator(TestCase):
    def test_valid_true(self):
        message = SmartAppFromMessage({"messageName": "test"}, headers=[])
        validator = MockMessageValidator()
        validator.validate(message)

    def test_valid_false(self):
        message = SmartAppFromMessage({"messageName": "no_test"}, headers=[])
        validator = MockMessageValidator()
        with self.assertRaises(validator.VALIDATOR_EXCEPTION):
            validator.validate(message)

    def test_valid_false_log(self):
        fh = logging.StreamHandler()
        logging.root.handlers = []
        logging.root.addHandler(fh)
        logging.root.setLevel('INFO')
        fh.handle = Mock()

        message = SmartAppFromMessage({"messageName": "no_test"}, headers=[])
        validator = MockMessageValidator(on_exception="log")
        try:
            validator.validate(message)
        except validator.VALIDATOR_EXCEPTION:
            raise self.failureException("Validator raised exception")

        fh.handle.assert_called()
        log_record = fh.handle.call_args[0][0]
        self.assertIn(MockMessageValidator.__name__, log_record.getMessage())
