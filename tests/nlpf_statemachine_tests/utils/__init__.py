"""
# Модуль Test Utils.

--- это коллекция полезных утилит для написания тестов поверх приложений на NLPF StateMachine.

Данный модуль будет самостоятельной библиотекой, которая планируется к сборке и публикации
независимо от модуля NLPF StateMachine.
"""

from .base import AnyObj, assert_action_call, random_guid, random_string
from .mocks import TestsCore, action_integration_mock, action_mock, action_with_exception_mock, classifier_mock
from .test_case import SMTestCase, SMTestCaseBase

__version__ = "0.0.1"

__all__ = [
    __version__,
    AnyObj,
    SMTestCase,
    SMTestCaseBase,
    TestsCore,
    action_integration_mock,
    action_mock,
    action_with_exception_mock,
    assert_action_call,
    classifier_mock,
    random_guid,
    random_string,
]
