"""
# Локальные утилиты для тестов.
"""
from __future__ import annotations

from unittest.mock import MagicMock


def classifier_mock(run_mock: str | None = None, run_legacy_mock: str | None = None) -> MagicMock:
    """
    ## Генерация классификатора.

    Args:
        run_mock (str): return_value для метода run;
        run_legacy_mock: return_value для метода run_legacy.

    Returns:
        MagicMock: мок классификатора.
    """
    classifier = MagicMock()
    classifier.run.return_value = run_mock
    classifier.run_legacy.return_value = run_legacy_mock
    return classifier
