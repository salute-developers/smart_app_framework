import os
import platform
import sys

from setuptools import find_packages, setup

import versioneer

with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()


def tf_version():
    if sys.platform == "darwin" and platform.machine() == "arm64":
        return "tensorflow-macos==2.6.0"
    elif sys.platform == "darwin" and platform.machine() == "x86_64":
        return "tensorflow==2.6.0"
    elif sys.platform == "linux" and platform.machine() == "x86_64":
        return "tensorflow==2.6.0"
    elif sys.platform == "linux" and platform.machine() == "aarch64":
        return "tensorflow-aarch64==2.6.0"
    return "tensorflow==2.6.0"


setup(
    name=os.getenv("PACKAGE_NAME", default="smart_app_framework"),
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Salute-Developers",
    description="SmartApp Framework — это фреймворк, "
                "который позволяет создавать смартапы "
                "с поддержкой виртуальных ассистентов Салют.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=[]),
    include_package_data=True,
    install_requires=[
        "aiohttp==3.7.4",
        "aioredis==2.0.0",
        "boto==2.49.0",
        "confluent_kafka==1.9.2",
        "croniter==1.3.7",
        "dawg==0.8.0",
        "dill==0.3.3",
        "ics==0.6",
        "Jinja2==3.0.3",
        "keras==2.6.0",
        "nltk==3.5",
        "numpy==1.19.3",
        "objgraph==3.4.1",
        "prometheus-client==0.7.1",
        "psutil==5.8.0",
        "pyignite==0.5.2",
        "pymorphy2==0.8",
        "pymorphy2_dicts==2.4.393442.3710985",
        "python-dateutil==2.7.3",
        "python-json-logger==0.1.11",
        "PyYAML==5.3",
        "redis==4.1.4",
        "requests==2.22.0",
        "rusenttokenize==0.0.5",
        "scikit-learn==1.1.2",
        "setuptools==62.3.2",
        "tabulate==0.9.0",
        "tatsu==4.4.0",
        "grpcio==1.49.1",  # library for tensorflow
        "oauthlib==3.2.0",  # library for tensorflow
        "google-auth==2.12.0",  # library for tensorflow
        tf_version(),
        "timeout-decorator==0.4.1",
        "tqdm==4.64.1",
        "incremental==21.3.0",  # library for Twisted
        "Twisted==22.8.0",
        "freezegun==1.1.0",
        "protobuf==3.19.6"  # https://developers.google.com/protocol-buffers/docs/news/2022-05-06#python-updates
    ],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9"
    ]
)
