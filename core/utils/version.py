from typing import Optional

import importlib.metadata


def _get_distribution_safe(name: str) -> Optional[importlib.metadata.Distribution]:
    try:
        distribution = importlib.metadata.distribution(name)
        return distribution
    except importlib.metadata.PackageNotFoundError:
        return None


def get_nlpf_version() -> Optional[str]:
    distribution = _get_distribution_safe("sber-nlp-platform-smart-app-framework")
    if distribution is None:
        distribution = _get_distribution_safe("smart-app-framework")
    nlpf_version = distribution.version if distribution is not None else None
    return nlpf_version
