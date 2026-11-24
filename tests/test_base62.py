import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_round_trip_values(self):
        for value in (0, 1, 61, 62, 3844, 2**64):
            with self.subTest(value=value):
                self.assertEqual(decode(encode(value)), value)

    def test_zero_encodes_as_zero(self):
        self.assertEqual(encode(0), "0")

    def test_digit_order(self):
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")

    def test_encode_rejects_negative_and_non_integer_values(self):
        for value, error in ((-1, ValueError), (True, TypeError), (1.5, TypeError)):
            with self.subTest(value=value):
                with self.assertRaises(error):
                    encode(value)

    def test_decode_rejects_empty_and_invalid_input(self):
        for code in ("", "a-", "é"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    decode(code)

    def test_decode_rejects_non_string_values(self):
        with self.assertRaises(TypeError):
            decode(42)


if __name__ == "__main__":
    unittest.main()
