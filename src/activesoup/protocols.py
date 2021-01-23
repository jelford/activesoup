from typing import Any, Optional

import requests

try:
    from typing import Protocol
except ImportError:
    # Older python versions will not have Protocol available
    class Protocol:  # type: ignore
        pass


class ActiveSoupResult(Protocol):
    @property
    def url(self) -> str:
        ...

    def __getitem__(self, lookup: str) -> Any:
        ...


class Resolver(Protocol):
    def resolve(self, response: requests.Response) -> ActiveSoupResult:
        ...


class Driver(Protocol):
    def __enter__(self) -> "Driver":
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    def get(self, url, **kwargs) -> "Driver":
        ...

    @property
    def url(self) -> Optional[str]:
        ...

    def __getattr__(self, item: str) -> Any:
        ...

    def __getitem__(self, item) -> Any:
        ...
