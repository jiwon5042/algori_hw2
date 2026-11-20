import http.client
from threading import Thread
import unittest
from urllib.parse import urlencode

from src.server import create_server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(host="127.0.0.1", port=0)
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, body=None):
        connection = http.client.HTTPConnection(self.host, self.port)
        headers = {}
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        result = response.status, response.getheaders(), response.read()
        connection.close()
        return result

    def test_home_and_table_pages_render(self):
        status, _, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b'name="url"', body)

        self.request("POST", "/shorten", urlencode({"url": "https://example.com"}))
        status, _, body = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn(b"Horner", body)
        self.assertIn(b"URLs to codes", body)

    def test_post_creates_short_url_and_redirects_without_following(self):
        url = "https://example.com/path?a=1&b=2"
        body = urlencode({"url": url})
        status, _, response_body = self.request("POST", "/shorten", body)
        self.assertEqual(status, 200)
        self.assertIn(b"/s/0", response_body)
        self.assertIn(b"&amp;", response_body)

        status, headers, response_body = self.request("GET", "/s/0")
        self.assertEqual(status, 302)
        self.assertEqual(dict(headers)["Location"], url)
        self.assertEqual(response_body, b"")

    def test_invalid_urls_and_missing_codes_return_errors(self):
        body = urlencode({"url": "javascript:alert(1)"})
        status, _, _ = self.request("POST", "/shorten", body)
        self.assertEqual(status, 400)

        status, _, _ = self.request("GET", "/s/unknown")
        self.assertEqual(status, 404)
        status, _, _ = self.request("GET", "/missing")
        self.assertEqual(status, 404)

    def test_malformed_and_oversized_forms_are_rejected(self):
        status, _, _ = self.request("POST", "/shorten", "not-a-form")
        self.assertEqual(status, 400)

        connection = http.client.HTTPConnection(self.host, self.port)
        connection.request(
            "POST",
            "/shorten",
            body=b"x" * 16_385,
            headers={"Content-Length": "16385"},
        )
        response = connection.getresponse()
        self.assertEqual(response.status, 413)
        response.read()
        connection.close()


if __name__ == "__main__":
    unittest.main()
