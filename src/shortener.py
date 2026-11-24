"""In-memory URL shortening backed by custom hash tables."""

from urllib.parse import urlsplit
from typing import Callable

from src.base62 import encode
from src.hash_table import HashTable, HashTableBackend


class URLShortener:
    def __init__(
        self,
        hash_table_class: Callable[..., HashTableBackend[str]] = HashTable,
        table_capacity: int = 101,
    ):
        self.by_url: HashTableBackend[str] = hash_table_class(capacity=table_capacity)
        self.by_code: HashTableBackend[str] = hash_table_class(capacity=table_capacity)
        self._next_id = 0

    @staticmethod
    def _validate_url(url: str) -> None:
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if not url or any(
            character.isspace() or ord(character) < 0x20 or ord(character) == 0x7F
            for character in url
        ):
            raise ValueError("url must be non-empty and contain no whitespace")

        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as error:
            raise ValueError("url must be a valid HTTP or HTTPS URL") from error

        if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc or not hostname:
            raise ValueError("url must be a valid HTTP or HTTPS URL")

    def shorten(self, url: str) -> str:
        self._validate_url(url)
        if self.by_url.contains(url):
            return self.by_url.get(url)

        code = encode(self._next_id)
        self.by_url.set(url, code)
        self.by_code.set(code, url)
        self._next_id += 1
        return code

    def expand(self, code: str) -> str:
        return self.by_code.get(code)
