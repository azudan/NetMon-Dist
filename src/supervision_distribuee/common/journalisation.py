from __future__ import annotations

import logging


def configurer_logging(niveau: int = logging.INFO) -> None:
    logging.basicConfig(
        level=niveau,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )