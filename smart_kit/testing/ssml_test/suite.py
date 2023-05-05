import re
import requests
from lxml import etree
from typing import Tuple, Dict, Callable, Any, List, Optional


from core.logging.logger_utils import log
from smart_kit.resources import SmartAppResources
from smart_kit.testing.ssml_test.ssml_string_parser import ssml_string_parser
from smart_kit.utils.object_location import ObjectLocation


class SsmlTestSuite:
    def __init__(self, ssml_test_url: str):
        self.ssml_checker = SsmlChecker(ssml_test_url)

    def test_single_string(self, string_to_test: str) -> None:
        print(f"[+] Testing SSML string \"{string_to_test}\"")
        self._check_and_print(string_to_test)

    def test_statics(
            self,
            resources: SmartAppResources,
            ssml_resources: List[str]
    ) -> bool:
        ssml_strings = self.collect_ssml_strings(resources, ssml_resources)
        success_num = 0
        for ssml_string, location in ssml_strings:
            print(f"[+] Testing SSML string \"{ssml_string}\" from {location}")
            success_num += self._check_and_print(ssml_string)
        print(f"[+] Total: {success_num}/{len(ssml_strings)}")
        return success_num == len(ssml_strings)

    def collect_ssml_strings(
            self,
            resources: SmartAppResources,
            ssml_resources: List[str]
    ) -> List[Tuple[str, ObjectLocation]]:
        """Returns list of tuples of parsed ssml-string and their locations"""
        ssml_strings = []
        for resource_name in ssml_resources:
            resource = resources.get(resource_name)
            if resource:
                extracted_strings = ssml_string_parser(resource, ObjectLocation([resource_name]))
                ssml_strings.extend(extracted_strings)
            else:
                log(f"{resource_name} do not exist in resources", level="WARNING")
        return ssml_strings

    def _check_and_print(self, string_to_test: str) -> bool:
        template_span = self._get_template_span(string_to_test)
        if template_span:
            print(f"Warning: the string seems to have a template part in span {template_span}. In runtime the string's "
                  "validity may change.")
        is_valid, message = self.ssml_checker(string_to_test)
        if is_valid:
            print("[+] OK")
        else:
            print(f"[!] SSML markup of the string is invalid. Message: \"{message}\"")
        return is_valid

    def _get_template_span(self, string) -> Optional[Tuple[int, int]]:
        match = re.search("{{.*}}", string)
        if match:
            return match.span()
        return None


class SsmlChecker:
    parser = etree.XMLParser(schema=etree.XMLSchema(etree.XML(
        '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"><xsd:element name="speak"/></xsd:schema>'
    )))

    def __init__(self, ssml_checker_url: str):
        self.ssml_checker_url = ssml_checker_url

    def __call__(self, string_to_test: str) -> Tuple[bool, str]:
        """Returns whether ssml_string is valid and message describing invalidity"""
        for checker in (self._check_format, self._check_with_api):
            is_valid, err_msg = checker(string_to_test)
            if not is_valid:
                return is_valid, err_msg
        return True, ""

    def _check_format(self, string_to_test: str) -> Tuple[bool, str]:
        try:
            etree.fromstring(string_to_test, self.parser)
            return True, ""
        except etree.XMLSyntaxError as e:
            return False, str(e)

    def _check_with_api(self, string_to_test: str) -> Tuple[bool, str]:
        try:
            response_json = requests.post(self.ssml_checker_url,
                                          data=string_to_test.encode("utf-8"),
                                          headers={"Content-Type": "application/ssml"}).json()
            return response_json["is_valid"], response_json.get("error", "")
        except requests.exceptions.ConnectionError:
            print("Cannot connect to ssml check server. Skipping online test.")
            return True, ""
