from typing import Tuple, Dict, Callable, Any, List

from lxml import etree

from core.logging.logger_utils import log
from smart_kit.resources import SmartAppResources
from smart_kit.utils.object_location import ObjectLocation


class SsmlTestSuite:
    def __init__(self, ssml_test_url: str):
        self.ssml_checker = SsmlChecker(ssml_test_url)

    def test_single_string(self, string_to_test: str) -> None:
        self._check_and_print(string_to_test)

    def test_statics(
            self,
            resources: SmartAppResources,
            resource_to_ssml_string_parser: Dict[str, Callable[[Any, ObjectLocation], List[Tuple[str, ObjectLocation]]]]
    ):
        ssml_strings = self.collect_ssml_strings(resources, resource_to_ssml_string_parser)
        success_num = 0
        for ssml_string, location in ssml_strings:
            print(f"[+] Testing SSML string \"{ssml_string}\" from {location}")
            success_num += self._check_and_print(ssml_string)
        print(f"[+] Total: {success_num}/{len(ssml_strings)}")

    def collect_ssml_strings(
            self,
            resources: SmartAppResources,
            resource_ssml_string_parsers: Dict[str, Callable[[Any, ObjectLocation], List[Tuple[str, ObjectLocation]]]]
    ) -> List[Tuple[str, ObjectLocation]]:
        """Returns list of tuples of parsed ssml-string and its location"""
        ssml_strings = []
        for resource_name, ssml_extractor in resource_ssml_string_parsers.items():
            resource = resources.get(resource_name)
            if resource:
                extracted_strings = ssml_extractor(resource, ObjectLocation([resource_name]))
                ssml_strings.extend(extracted_strings)
            else:
                log(f"{resource_name} do not exist in resources", level="WARNING")
        return ssml_strings

    def _check_and_print(self, string_to_test: str) -> bool:
        is_valid, message = self.ssml_checker(string_to_test)
        if is_valid:
            print("[+] OK")
        else:
            print(f"[!] SSML markup of the string is invalid. Message: \"{message}\"")
        return is_valid


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
        # TODO: update according to contract
        # response_json = requests.get(f"{self.ssml_checker_url}/{string_to_test}").json()
        # return response_json["is_valid"], response_json.get("message", "")
        return True, ""  # TODO
