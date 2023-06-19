import argparse
import os
import shutil
import sys

import smart_kit
from core.descriptions.descriptions import Descriptions
from smart_kit.management.base import AppCommand, init_logger
from smart_kit.testing.ssml_test.suite import SsmlTestSuite
from smart_kit.testing.suite import TestSuite


def define_path(path):
    if os.path.exists(path):
        return path
    folder, _ = os.path.split(sys.argv[0])
    return os.path.join(folder, path)


class TestsCommand(AppCommand):
    """Command for testing scenarios and ssml strings in app"""

    TEST_TEMPLATE_PATH = "test_template.json"
    smart_kit_path = smart_kit.__path__[0]
    DEFAULT_TEMPLATE_PATH = os.path.join(smart_kit_path, "template/static/references/test_template.json")
    DEFAULT_PREDEFINED_FIELDS_STORAGE = os.path.join(
        smart_kit_path, "template/static/references/predefined_fields_storage.json")
    TEST_EXTENSION = ".json"

    def __init__(self, app_config):
        self.app_config = app_config
        self.ssml_suite = SsmlTestSuite(self.app_config.SSML_TEST_ADDRESS)
        self.parser = argparse.ArgumentParser(description="Scenario tests creating and running.")
        self.parser.add_argument("path", metavar="PATH", type=str, help="Path to directory with tests", action="store",
                                 nargs="?", default="")
        self.parser.add_argument("predefined_fields_storage", metavar="PREDEFINED_FIELDS_STORAGE", type=str,
                                 help="Path to json file with stored predefined fields", action="store", nargs="?",
                                 default=str(self.DEFAULT_PREDEFINED_FIELDS_STORAGE))
        self.commands = self.parser.add_mutually_exclusive_group(required=True)
        self.commands.add_argument("--run", dest="run", help="Runs Tests", action="store_true")
        run_command = self.parser.add_argument_group("Running")
        run_command.add_argument("--make-csv", dest="make_csv", help="Create csv file for tests results",
                                 action="store_true")
        run_command.add_argument("--ssml-off", dest="ssml_off", help="Do not run SSML tests", action="store_true")
        run_command.add_argument("--scenarios-off", dest="scenarios_off", help="Do not run scenarios tests",
                                 action="store_true")
        run_command.add_argument("--ssml-interactive", dest="ssml_interactive",
                                 help="Interactive mode of checking SSML strings", action="store_true")

        self.commands.add_argument(
            "--gen", dest="gen", help="Create test directory at provided path", action="store_true"
        )
        gen_command = self.parser.add_argument_group("Generating")
        gen_command.add_argument(
            "--update", dest="update", help="Create missing template for scenarios", action="store_true",
        )

    def execute(self, *args, **kwargs) -> None:
        init_logger(self.app_config)
        namespace = self.parser.parse_args(args)
        if namespace.gen:
            if not namespace.path:
                self.parser.error("Tests generation utility require path")
            self.generate_tests_folder(namespace.path, namespace.update)
        elif namespace.run:
            if namespace.ssml_interactive:
                if namespace.scenarios_off or namespace.ssml_off or namespace.make_csv:
                    self.parser.error("--ssml-interactive and --scenarios-off|--ssml-off|--make-csv are mutually "
                                      "exclusive")
                self.run_interactive_ssml_tests()
            else:
                tests_ok = True
                if not namespace.scenarios_off:
                    if not namespace.path:
                        self.parser.error("Scenario tests require path")
                    print("Testing scenarios...")
                    tests_ok = self.run_scenario_tests(namespace.path, namespace.predefined_fields_storage,
                                                       namespace.make_csv)
                    print("Testing scenarios done\n")
                else:
                    print("Scenarios tests are off. Skipping them.")
                if not namespace.ssml_off:
                    print("Testing SSML strings...")
                    tests_ok = self.run_ssml_tests() and tests_ok
                    print("Testing SSML strings done\n")
                else:
                    print("SSML tests are off. Skipping them.")
                if not tests_ok:
                    sys.exit(1)
        else:
            raise Exception("Something going wrong due parsing the args")

    def generate_tests_folder(self, path: str, update=False) -> None:
        settings = self.app_config.SETTINGS(
            config_path=self.app_config.CONFIGS_PATH, secret_path=self.app_config.SECRET_PATH,
            references_path=self.app_config.REFERENCES_PATH, app_name=self.app_config.APP_NAME
        )
        resources = self.app_config.RESOURCES(settings.get_source(), self.app_config.REFERENCES_PATH, settings)
        scenario_names = Descriptions(resources.registered_repositories)["scenarios"].keys()
        folder_path = define_path(path)

        try:
            os.mkdir(folder_path)
            print(f"[+] Created tests folder at: {folder_path}")
        except FileExistsError:
            if not update:
                raise
            print(f"[+] Update tests folder at: {folder_path}")

        with open(self.get_test_template_path(), "r") as template_file:
            for scen_name in scenario_names:
                template_file.seek(0)
                new_file_path = os.path.join(folder_path, scen_name + self.TEST_EXTENSION)
                try:
                    with open(new_file_path, "x") as new_test_file:
                        shutil.copyfileobj(template_file, new_test_file)
                        print(f"[+] Created template file {new_file_path}")
                except FileExistsError:
                    if not update:
                        raise

    def run_scenario_tests(self, path, predefined_fields_storage, make_csv) -> bool:
        path = define_path(path)
        predefined_fields_storage = define_path(predefined_fields_storage)
        if not os.path.exists(path):
            print(f"[!] Tests folder does not found at {path}")
            return False
        elif not os.path.exists(predefined_fields_storage):
            print(f"[!] Predefined fields storage file does not found, check file path: {predefined_fields_storage}")
            return False
        else:
            return TestSuite(path, self.app_config, predefined_fields_storage, make_csv).run()

    def run_ssml_tests(self) -> bool:
        settings = self.app_config.SETTINGS(
            config_path=self.app_config.CONFIGS_PATH, secret_path=self.app_config.SECRET_PATH,
            references_path=self.app_config.REFERENCES_PATH, app_name=self.app_config.APP_NAME)
        source = settings.get_source()
        resources = self.app_config.RESOURCES(source, self.app_config.REFERENCES_PATH, settings)
        ssml_resources = self.app_config.SSML_RESOURCES
        return self.ssml_suite.test_statics(resources, ssml_resources)

    def run_interactive_ssml_tests(self) -> None:
        prompt = input("Enter ssml string to check (leave empty to exit):\n> ")
        while prompt:
            self.ssml_suite.test_single_string(prompt)
            prompt = input("> ")

    def get_test_template_path(self) -> str:
        path = os.path.join(self.app_config.REFERENCES_PATH, self.TEST_TEMPLATE_PATH)
        if not os.path.exists(path):
            print(f"[!] Template for test file does not found. Expected at path {path}. Using default")
            path = self.DEFAULT_TEMPLATE_PATH
        return path
