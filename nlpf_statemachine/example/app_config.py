"""
# NLPF APP configs.
"""
import os
import sys

from nlpf_statemachine.example.app.model_config import ExampleResources
from nlpf_statemachine.example.app.user import ExampleUser
from nlpf_statemachine.override import SMDialogueManager, SMSmartAppModel
from smart_kit.start_points.main_loop_kafka import MainLoop

SYSTEM_NAME = "example"

path = os.path.abspath(__file__)
APP_NAME = os.environ.get("SCENARIO_APP_NAME")
APP_NAME = APP_NAME or os.path.dirname(path).split("/")[-1] or SYSTEM_NAME
APP_NAME = APP_NAME.replace("-", "_")

if os.environ.get("STATIC_PATH"):
    setattr(sys.modules[__name__], "STATIC_PATH", os.environ["STATIC_PATH"])
if os.environ.get("SECRET_PATH"):
    setattr(sys.modules[__name__], "SECRET_PATH", os.environ["SECRET_PATH"])

MODE = "debug"
NORMALIZER_ADDRESS = "http://intent-recognizer-ci01808661-dev-sbernlpdemo.apps.test-ose.sigma.sbrf.ru"
AUTO_LISTENING = False
MAIN_LOOP = MainLoop

# Для StateMachine
USER = ExampleUser
RESOURCES = ExampleResources
DIALOGUE_MANAGER = SMDialogueManager
MODEL = SMSmartAppModel
