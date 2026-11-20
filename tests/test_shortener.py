import unittest

from src.shortener import URLShortener


class URLShortenerTests(unittest.TestCase):
    def test_shortens_and_expands_urls(self):
        shortener = URLShortener()
        code = shortener.shorten("https://example.com/a?b=1")
        self.assertEqual(code, "0")
        self.assertEqual(shortener.expand(code), "https://example.com/a?b=1")

    def test_same_url_reuses_code_and_new_urls_get_sequential_codes(self):
        shortener = URLShortener()
        first = shortener.shorten("https://example.com")
        self.assertEqual(shortener.shorten("https://example.com"), first)
        self.assertEqual(shortener.shorten("http://example.org"), "1")

    def test_rejects_malformed_or_unsupported_urls(self):
        shortener = URLShortener()
        for url in (
            "",
            "example.com",
            "ftp://example.com",
            "https:///missing-host",
            "https://example.com/with space",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)

    def test_rejects_non_string_url(self):
        with self.assertRaises(TypeError):
            URLShortener().shorten(42)

    def test_unknown_codes_raise_key_error(self):
        with self.assertRaises(KeyError):
            URLShortener().expand("unknown")


if __name__ == "__main__":
    unittest.main()
