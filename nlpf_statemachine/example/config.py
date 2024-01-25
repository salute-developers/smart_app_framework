"""
# Установка дефолтных конфигов.
"""
import os

os.environ.setdefault("SMART_KIT_APP_CONFIG", "nlp_statemachine.example.app_config")
SMART_KIT_APP_CONFIG = os.getenv("SMART_KIT_APP_CONFIG")
