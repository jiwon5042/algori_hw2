"""A fixed-capacity hash table that resolves collisions by linear probing."""

from typing import Generic, TypeVar


Value = TypeVar("Value")


class _Node(Generic[Value]):
    def __init__(self, key: str, value: Value):
        self.key = key
        self.value = value
        self.deleted = False


class LinearProbingHashTable(Generic[Value]):
    def __init__(self, capacity: int = 7):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self.buckets: list[_Node[Value] | None] = [None] * capacity
        self._size = 0
        self.last_probes = 0

    def _validate_key(self, key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    def explain_hash(self, key: str) -> tuple[int, tuple[int, ...]]:
        self._validate_key(key)
        value = 0
        steps = []
        for character in key:
            value = (31 * value + ord(character)) % self.capacity
            steps.append(value)
        return value, tuple(steps)

    def _probe(self, key: str) -> tuple[_Node[Value] | None, tuple[int, ...]]:
        home, _ = self.explain_hash(key)
        visited = []
        for offset in range(self.capacity):
            index = (home + offset) % self.capacity
            visited.append(index)
            node = self.buckets[index]
            if node is None:
                return None, tuple(visited)
            if not node.deleted and node.key == key:
                return node, tuple(visited)
        return None, tuple(visited)

    def probe_path(self, key: str) -> tuple[int, ...]:
        _, path = self._probe(key)
        return path

    def set(self, key: str, value: Value) -> None:
        home, _ = self.explain_hash(key)
        first_deleted = None
        probes = 0
        for offset in range(self.capacity):
            index = (home + offset) % self.capacity
            probes += 1
            node = self.buckets[index]
            if node is None:
                target = first_deleted if first_deleted is not None else index
                self.buckets[target] = _Node(key, value)
                self._size += 1
                self.last_probes = probes
                return
            if node.deleted:
                if first_deleted is None:
                    first_deleted = index
                continue
            if node.key == key:
                node.value = value
                self.last_probes = probes
                return

        if first_deleted is not None:
            self.buckets[first_deleted] = _Node(key, value)
            self._size += 1
            self.last_probes = probes
            return

        self.last_probes = probes
        raise OverflowError("hash table is full")

    def get(self, key: str) -> Value:
        node, path = self._probe(key)
        self.last_probes = len(path)
        if node is None:
            raise KeyError(key)
        return node.value

    def delete(self, key: str) -> None:
        node, path = self._probe(key)
        self.last_probes = len(path)
        if node is None:
            raise KeyError(key)
        node.deleted = True
        self._size -= 1

    def contains(self, key: str) -> bool:
        node, path = self._probe(key)
        self.last_probes = len(path)
        return node is not None

    def __len__(self) -> int:
        return self._size
