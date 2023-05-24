
from typing import Any


class ProxyError(Exception):
    pass


class ModelOverloaded(Exception):
    def __init__(self, reason: Any) -> None:
        self.reason = reason