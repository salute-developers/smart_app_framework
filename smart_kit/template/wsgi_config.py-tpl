#!/usr/bin/env python3
# Скрипт конфигурации навыка при запуске утилитой gunicorn в режиме run_app для работы по HTTP
import os

bind = '0.0.0.0:8000'
workers = os.cpu_count() * 2 + 1
preload_app = True


# Server Hooks
def on_starting(server):
    print("SERVER STARTING...")
