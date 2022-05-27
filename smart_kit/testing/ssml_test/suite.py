
from typing import Tuple, Dict, Callable, Any, List

import requests

from core.logging.logger_utils import log
from smart_kit.resources import SmartAppResources
from smart_kit.utils.object_location import ObjectLocation


class SsmlTestSuite:
    def __init__(self, ssml_test_url: str):
        self.ssml_test_url = ssml_test_url

    def test_single_string(self, string_to_test: str):
        is_valid, message = self.check_ssml_string(string_to_test, self.ssml_test_url)
        if is_valid:
            print(f"[+] OK")
        else:
            print(f"[!] SSML markup of the string is invalid. Message: \"{message}\"")

    def test_statics(self,
                     resources: SmartAppResources,
                     resource_to_ssml_string_parser: Dict[str, Callable[[Any, ObjectLocation],
                                                                        List[Tuple[str, ObjectLocation]]]]):
        ssml_strings = self.collect_ssml_strings(resources, resource_to_ssml_string_parser)
        success_num = 0
        total_num = len(ssml_strings)
        for ssml_string, location in ssml_strings:
            print(f"[+] Testing SSML string {ssml_string} from {location}")
            print(f"[+] OK")
            is_valid, message = self.check_ssml_string(ssml_string, self.ssml_test_url)
            if is_valid:
                success_num += 1
            else:
                print(f"[!] SSML markup of the string is invalid. Message: {message}")
        print(f"[+] Total: {success_num}/{total_num}")

    def collect_ssml_strings(
            self,
            resources: SmartAppResources,
            resource_ssml_string_parsers: Dict[str, Callable[[Any, ObjectLocation], List[Tuple[str, ObjectLocation]]]]) \
            -> List[Tuple[str, ObjectLocation]]:
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

    def check_ssml_string(self, string_to_test: str, ssml_checker_url: str) -> Tuple[bool, str]:
        """Returns whether ssml_string is valid and message describing invalidity"""
        # TODO: insert ssml_string as parameter according to API
        response = requests.get(f"{ssml_checker_url}/{string_to_test}")
        if not response:
            raise Exception(f"Error during connecting to {ssml_checker_url}\n"
                            f"Status: {response.status_code}\n"
                            f"Reason: {response.reason}")
        response_json = response.json()
        is_valid = response_json["is_valid"]
        if is_valid:
            return True, ""
        else:
            message = response_json["message"]
            return False, message
