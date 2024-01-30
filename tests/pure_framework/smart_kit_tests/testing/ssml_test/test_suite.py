# coding: utf-8
import unittest
from unittest.mock import Mock, patch

from smart_kit.testing.ssml_test.suite import SsmlChecker


class SsmlCheckerTest1(unittest.IsolatedAsyncioTestCase):
    async def test_format_no_root(self):
        string_to_test = "hi <speak></speak> there"
        expected_answer = False, 'line 1: b"Start tag expected, \'<\' not found" (line 1)'
        ssml_checker_url = ""
        checker = SsmlChecker(ssml_checker_url)
        self.assertEqual(expected_answer, checker(string_to_test))

    async def test_format_wrong_speak(self):
        string_to_test = "<speakk></speakk>"
        expected_answer = False, "Element 'speakk': No matching global declaration " \
                                 "available for the validation root. (<string>, line 0)"
        ssml_checker_url = ""
        checker = SsmlChecker(ssml_checker_url)
        self.assertEqual(expected_answer, checker(string_to_test))

    async def test_format_wrong_xml(self):
        string_to_test = "<speak><a></b></speak>"
        expected_answer = False, "line 1: b'Opening and ending tag mismatch: a line 1 and b' (line 1)"
        ssml_checker_url = ""
        checker = SsmlChecker(ssml_checker_url)
        self.assertEqual(expected_answer, checker(string_to_test))

    async def test_format_non_xml_symbol(self):
        string_to_test = "<speak>a & b</speak>"
        expected_answer = False, "line 1: b'xmlParseEntityRef: no name' (line 1)"
        ssml_checker_url = ""
        checker = SsmlChecker(ssml_checker_url)
        self.assertEqual(expected_answer, checker(string_to_test))

    @patch("requests.post")
    async def test_api_false(self, request_mock: Mock):
        string_to_test = "<speak><a></a></speak>"
        expected_answer = False, " Validity error: Element 'a': This element is not expected. Expected is one of ( " \
                                 "meta, metadata, lexicon, ##other*, aws, token, w, voice, prosody, audio ). "
        request_mock.return_value = Mock(json=lambda: {
            "is_valid": False, "error": " Validity error: Element 'a': This element is not expected. Expected is one of"
                                        " ( meta, metadata, lexicon, ##other*, aws, token, w, voice, prosody, audio ). "
        })
        ssml_checker_url = ""
        checker = SsmlChecker(ssml_checker_url)
        self.assertEqual(expected_answer, checker(string_to_test))

    @patch("requests.post")
    async def test_true(self, request_mock: Mock):
        string_to_test = "<speak><a></a></speak>"
        expected_answer = True, ""
        request_mock.return_value = Mock(json=lambda: {"is_valid": True})
        ssml_checker_url = ""
        checker = SsmlChecker(ssml_checker_url)
        self.assertEqual(expected_answer, checker(string_to_test))
