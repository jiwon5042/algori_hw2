import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_empty_table_has_no_entries(self):
        table = HashTable()
        self.assertEqual(len(table), 0)
        self.assertFalse(table.contains("missing"))

    def test_insert_update_and_lookup(self):
        table = HashTable()
        table.set("name", "Ada")
        table.set("name", "Grace")
        self.assertEqual(table.get("name"), "Grace")
        self.assertEqual(len(table), 1)
        self.assertTrue(table.contains("name"))

    def test_chaining_handles_collisions(self):
        table = HashTable(capacity=3)
        table.set("a", 1)
        table.set("d", 2)
        self.assertEqual(table.get("a"), 1)
        self.assertEqual(table.get("d"), 2)
        self.assertEqual(len(table), 2)

    def test_delete_removes_only_requested_key(self):
        table = HashTable(capacity=3)
        table.set("a", 1)
        table.set("d", 2)
        table.delete("a")
        self.assertFalse(table.contains("a"))
        self.assertEqual(table.get("d"), 2)
        self.assertEqual(len(table), 1)

    def test_missing_keys_raise_key_error(self):
        table = HashTable()
        with self.assertRaises(KeyError):
            table.get("missing")
        with self.assertRaises(KeyError):
            table.delete("missing")

    def test_empty_key_and_none_value_are_supported(self):
        table = HashTable()
        table.set("", None)
        table.set("키/🙂", "unicode")
        self.assertTrue(table.contains(""))
        self.assertIsNone(table.get(""))
        self.assertEqual(table.get("키/🙂"), "unicode")

    def test_lookup_records_number_of_compared_nodes(self):
        table = HashTable(capacity=3)
        table.set("a", 1)
        table.set("d", 2)
        self.assertEqual(table.get("d"), 2)
        self.assertEqual(table.last_probes, 2)
        self.assertFalse(table.contains("g"))
        self.assertEqual(table.last_probes, 2)

    def test_hash_explanation_reports_horner_steps(self):
        table = HashTable(capacity=7)
        index, steps = table.explain_hash("abc")
        self.assertEqual(index, 6)
        self.assertEqual(steps, (6, 4, 6))

    def test_invalid_capacity_and_key_types_are_rejected(self):
        for capacity in (0, -1, True):
            with self.subTest(capacity=capacity):
                with self.assertRaises(ValueError):
                    HashTable(capacity=capacity)
        with self.assertRaises(TypeError):
            HashTable().set(1, "value")


if __name__ == "__main__":
    unittest.main()
