# coding: utf-8
import unittest

from smart_kit.testing.ssml_test.ssml_string_parser import ssml_string_parser
from smart_kit.utils.object_location import ObjectLocation


class SsmlStringParserTest1(unittest.IsolatedAsyncioTestCase):
    async def test_parse(self):
        expected_ssml = "<speak>С помощью <say-as interpret-as=\"spell-out\">SSML</say-as> разметки я умею делать " \
                        "<break time=\"2s\" /> паузы, <break /> произносить слова по <say-as " \
                        "interpret-as=\"characters\">буквам</say-as> и многое другое.</speak>"
        expected_location = ObjectLocation(["scenarios", "tell_me_more_scenario", "actions", "[1]", "nodes",
                                            "pronounceText"])
        obj = {
            "tell_me_more_scenario": {
                "actions": [
                    {
                        "type": "string",
                        "command": "ANSWER_TO_USER",
                        "nodes": {
                            "pronounceText": "Сейчас я тебе всё расскажу!",
                            "items": [
                                {
                                    "bubble": {
                                        "text": "Сейчас я тебе всё расскажу!"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "type": "string",
                        "command": "ANSWER_TO_USER",
                        "nodes": {
                            "pronounceTextType": "application/ssml",
                            "pronounceText": "<speak>С помощью <say-as interpret-as=\"spell-out\">SSML</say-as> "
                                             "разметки я умею делать <break time=\"2s\" /> паузы, <break /> "
                                             "произносить слова по <say-as "
                                             "interpret-as=\"characters\">буквам</say-as> и многое другое.</speak>",
                            "items": [
                                {
                                    "bubble": {
                                        "text": "С помощью SSML-разметки я умею делать... паузы, произносить слова по "
                                                "б-у-к-в-а-м и многое другое. "
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "type": "run_scenario",
                        "scenario": "emotion_scenario"
                    }
                ]
            }
        }
        location = ObjectLocation(["scenarios"])
        actual_answer = ssml_string_parser(obj, location)
        self.assertEqual(1, len(actual_answer))
        self.assertEqual(expected_ssml, actual_answer[0][0])
        self.assertEqual(str(expected_location), str(actual_answer[0][1]))

    async def test_parse_ignore(self):
        expected_answer = []
        obj = {
            "tell_me_more_scenario": {
                "actions": [
                    {
                        "type": "string",
                        "command": "ANSWER_TO_USER",
                        "nodes": {
                            "pronounceText": "Сейчас я тебе всё расскажу!",
                            "items": [
                                {
                                    "bubble": {
                                        "text": "Сейчас я тебе всё расскажу!"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "type": "string",
                        "command": "ANSWER_TO_USER",
                        "no_ssml_check": True,
                        "nodes": {
                            "pronounceTextType": "application/ssml",
                            "pronounceText": "<speak>С помощью <say-as interpret-as=\"spell-out\">SSML</say-as> "
                                             "разметки я умею делать <break time=\"2s\" /> паузы, <break /> "
                                             "произносить слова по <say-as "
                                             "interpret-as=\"characters\">буквам</say-as> и многое другое.</speak>",
                            "items": [
                                {
                                    "bubble": {
                                        "text": "С помощью SSML-разметки я умею делать... паузы, произносить слова по "
                                                "б-у-к-в-а-м и многое другое. "
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "type": "run_scenario",
                        "scenario": "emotion_scenario"
                    }
                ]
            }
        }
        location = ObjectLocation(["scenarios"])
        actual_answer = ssml_string_parser(obj, location)
        self.assertEqual(expected_answer, actual_answer)
