#!/usr/bin/env python
"""
# Запуск NLPF Проекта.
"""
import sys

from core.logging.logger_utils import behaviour_log
from nlpf_statemachine.example.config import SMART_KIT_APP_CONFIG
from smart_kit.management.app_manager import execute_from_command_line

behaviour_log(f"SMART_KIT_APP_CONFIG = {SMART_KIT_APP_CONFIG}")

if __name__ == "__main__":
    command = input("Type command to manage.py: ")
    sys.argv = ["example/manage.py", command]
    execute_from_command_line(sys.argv)
else:
    execute_from_command_line(sys.argv)
