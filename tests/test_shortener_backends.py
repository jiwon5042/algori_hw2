import unittest

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable
from src.shortener import URLShortener


class ShortenerBackendTests(unittest.TestCase):
    def test_both_hash_tables_support_shortening_more_than_default_bucket_count(self):
        for table_class in (HashTable, LinearProbingHashTable):
            with self.subTest(table_class=table_class.__name__):
                shortener = URLShortener(hash_table_class=table_class)
                urls = [f"https://example.com/{index}" for index in range(20)]
                codes = [shortener.shorten(url) for url in urls]
                self.assertEqual(codes[0], "0")
                self.assertEqual(len(codes), len(set(codes)))
                for code, url in zip(codes, urls):
                    self.assertEqual(shortener.expand(code), url)


if __name__ == "__main__":
    unittest.main()
