"""A string-keyed hash table that resolves collisions with linked lists."""


class _Node:
    def __init__(self, key: str, value: object):
        self.key = key
        self.value = value
        self.next: _Node | None = None


class HashTable:
    def __init__(self, capacity: int = 7):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self.buckets: list[_Node | None] = [None] * capacity
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

    def _find(self, key: str) -> tuple[_Node | None, _Node | None, int]:
        index, _ = self.explain_hash(key)
        previous = None
        node = self.buckets[index]
        probes = 0
        while node is not None:
            probes += 1
            if node.key == key:
                return node, previous, probes
            previous = node
            node = node.next
        return None, previous, probes

    def set(self, key: str, value: object) -> None:
        node, previous, probes = self._find(key)
        self.last_probes = probes
        if node is not None:
            node.value = value
            return

        new_node = _Node(key, value)
        if previous is None:
            index, _ = self.explain_hash(key)
            self.buckets[index] = new_node
        else:
            previous.next = new_node
        self._size += 1

    def get(self, key: str) -> object:
        node, _, probes = self._find(key)
        self.last_probes = probes
        if node is None:
            raise KeyError(key)
        return node.value

    def delete(self, key: str) -> None:
        node, previous, probes = self._find(key)
        self.last_probes = probes
        if node is None:
            raise KeyError(key)

        index, _ = self.explain_hash(key)
        if previous is None:
            self.buckets[index] = node.next
        else:
            previous.next = node.next
        self._size -= 1

    def contains(self, key: str) -> bool:
        node, _, probes = self._find(key)
        self.last_probes = probes
        return node is not None

    def __len__(self) -> int:
        return self._size
