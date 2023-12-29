from unittest import TestCase

from core.utils.utils import mask_numbers


class TestMaskNumbers(TestCase):
    def test_1(self):
        masked_message = {
            "payload": {
                "pronounceText": "номер телефона: +79990000000",
                "items": [
                    {
                        "bubble": {
                            "text": "номер телефона: +7 (999) 000-00-00"
                        }
                    }
                ]
            }
        }

        mask_numbers(masked_message)
        self.assertEqual(masked_message["payload"]["pronounceText"], "номер телефона: +*number*")
        self.assertEqual(masked_message["payload"]["items"][0]["bubble"]["text"],
                         "номер телефона: +*number* (*number*) *number*-*number*-*number*")
