import unittest

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


def keys_for_home(capacity, home, count):
    helper = HashTable(capacity=capacity)
    keys = []
    candidate = 0
    while len(keys) < count:
        key = f"probe-{candidate}"
        if helper.explain_hash(key)[0] == home:
            keys.append(key)
        candidate += 1
    return keys


class LinearProbingHashTableTests(unittest.TestCase):
    def test_wraps_at_end_and_exposes_probe_path(self):
        table = LinearProbingHashTable(capacity=5)
        keys = keys_for_home(5, 4, 3)
        for value, key in enumerate(keys):
            table.set(key, value)

        self.assertEqual(table.probe_path(keys[2]), (4, 0, 1))
        self.assertEqual(table.get(keys[2]), 2)
        self.assertEqual(table.last_probes, 3)

    def test_delete_preserves_search_chain_and_reuses_tombstone(self):
        table = LinearProbingHashTable(capacity=5)
        keys = keys_for_home(5, 4, 4)
        for value, key in enumerate(keys[:3]):
            table.set(key, value)

        table.delete(keys[0])
        self.assertEqual(table.get(keys[2]), 2)
        self.assertEqual(table.last_probes, 3)
        table.set(keys[3], 3)
        self.assertEqual(table.get(keys[3]), 3)
        self.assertEqual(len(table), 3)

    def test_full_table_raises_and_deleted_slot_can_be_reused(self):
        table = LinearProbingHashTable(capacity=3)
        for key in ("a", "b", "c"):
            table.set(key, key)
        with self.assertRaises(OverflowError):
            table.set("d", "d")

        table.delete("b")
        table.set("d", "d")
        self.assertEqual(table.get("d"), "d")
        self.assertEqual(len(table), 3)

    def test_update_missing_keys_and_capacity_validation_match_interface(self):
        table = LinearProbingHashTable(capacity=5)
        table.set("key", 1)
        table.set("key", 2)
        self.assertEqual(table.get("key"), 2)
        self.assertEqual(len(table), 1)
        with self.assertRaises(KeyError):
            table.get("missing")
        with self.assertRaises(KeyError):
            table.delete("missing")
        with self.assertRaises(TypeError):
            table.set(42, "value")
        with self.assertRaises(ValueError):
            LinearProbingHashTable(capacity=0)


if __name__ == "__main__":
    unittest.main()
