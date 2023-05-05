from typing import Optional

import pkg_resources


def _get_distribution_safe(name: str) -> Optional[pkg_resources.DistInfoDistribution]:
    try:
        distribution = pkg_resources.get_distribution(name)
        return distribution
    except pkg_resources.DistributionNotFound:
        return None


def get_nlpf_version() -> Optional[str]:
    distribution = _get_distribution_safe("sber-nlp-platform-smart-app-framework")
    if distribution is None:
        distribution = _get_distribution_safe("smart-app-framework")
    nlpf_version = distribution.version if distribution is not None else None
    return nlpf_version
