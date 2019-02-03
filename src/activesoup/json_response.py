from typing import Any, Dict, List, Union

import requests


class JsonResponse:
    def __init__(self, raw_response: requests.Response) -> None:
        self.raw_response = raw_response
        self.json = raw_response.json()

    def __getitem__(
        self, name: Union[str, int]
    ) -> Union[str, int, Dict[str, Any], List[Any]]:
        return self.json[name]

    @property
    def url(self) -> str:
        return self.raw_response.url

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.json, attr)

    def __repr__(self) -> str:
        return "JsonResponse"

    def __str__(self) -> str:
        return "<[json]>"


class Resolver:
    def resolve(self, raw_response: requests.Response) -> JsonResponse:
        return JsonResponse(raw_response)
