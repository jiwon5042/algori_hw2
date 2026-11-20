"""HTTP interface for the in-memory URL shortener."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from urllib.parse import parse_qs, urlsplit

from src.hash_table import HashTable
from src.shortener import URLShortener


MAX_FORM_BYTES = 16_384


def _render_page(title: str, content: str) -> bytes:
    document = (
        "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
        f"<title>{escape(title)}</title>"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<style>body{font:16px sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}"
        "input{width:min(100%,36rem);padding:.5rem}button{padding:.5rem}"
        "code,pre{overflow-wrap:anywhere}li{margin:.5rem 0}</style>"
        f"<h1>{escape(title)}</h1>{content}</html>"
    )
    return document.encode("utf-8")


def _render_table(title: str, table: HashTable[str]) -> str:
    buckets = table.buckets
    content = [f"<h2>{escape(title)}</h2>", f"<p>Last lookup: {table.last_probes} nodes examined</p>"]
    content.append("<ol>")
    for index, head in enumerate(buckets):
        entries = []
        node = head
        while node is not None:
            calculated_index, steps = table.explain_hash(node.key)
            trace = "0" if not steps else " -> ".join(str(value) for value in steps)
            entries.append(
                "<li><code>"
                + escape(str(node.key))
                + "</code> = <code>"
                + escape(str(node.value))
                + f"</code>; Horner: {trace} (bucket {calculated_index})</li>"
            )
            node = node.next
        bucket_contents = "".join(entries) if entries else "<li>empty</li>"
        content.append(f"<li>Bucket {index}<ol>{bucket_contents}</ol></li>")
    content.append("</ol>")
    return "".join(content)


def _handler_for(shortener: URLShortener) -> type[BaseHTTPRequestHandler]:
    class RequestHandler(BaseHTTPRequestHandler):
        server_version = "URLShortener/1.0"

        def _send(self, status: int, body: bytes, content_type: str = "text/html; charset=utf-8") -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _send_page(self, status: int, title: str, content: str) -> None:
            self._send(status, _render_page(title, content))

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/":
                form = (
                    '<form action="/shorten" method="post">'
                    '<label for="url">URL</label><br>'
                    '<input id="url" name="url" type="url" required>'
                    '<button type="submit">Shorten</button></form>'
                    '<p><a href="/table">Inspect hash tables</a></p>'
                )
                self._send_page(200, "URL shortener", form)
                return

            if path == "/table":
                tables = (
                    _render_table("URLs to codes", shortener.by_url)
                    + _render_table("Codes to URLs", shortener.by_code)
                )
                self._send_page(200, "Hash table inspection", tables)
                return

            if path.startswith("/s/"):
                code = path.removeprefix("/s/")
                if not code or "/" in code:
                    self._send_page(404, "Not found", "<p>Unknown short code.</p>")
                    return
                try:
                    destination = shortener.expand(code)
                except KeyError:
                    self._send_page(404, "Not found", "<p>Unknown short code.</p>")
                    return

                self.send_response(302)
                self.send_header("Location", destination)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            self._send_page(404, "Not found", "<p>Page not found.</p>")

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/shorten":
                self._send_page(404, "Not found", "<p>Page not found.</p>")
                return

            length_value = self.headers.get("Content-Length")
            try:
                length = int(length_value) if length_value is not None else -1
            except ValueError:
                length = -1
            if length < 0:
                self._send_page(400, "Invalid request", "<p>Invalid Content-Length.</p>")
                return
            if length > MAX_FORM_BYTES:
                self._send_page(413, "Request too large", "<p>Form data is too large.</p>")
                return

            try:
                body = self.rfile.read(length).decode("utf-8")
                form = parse_qs(body, keep_blank_values=True, strict_parsing=True)
            except (UnicodeDecodeError, ValueError):
                self._send_page(400, "Invalid request", "<p>Malformed form data.</p>")
                return
            urls = form.get("url", [])
            if len(urls) != 1:
                self._send_page(400, "Invalid request", "<p>Provide exactly one URL.</p>")
                return

            url = urls[0]
            try:
                code = shortener.shorten(url)
            except (TypeError, ValueError) as error:
                message = escape(str(error))
                self._send_page(400, "Invalid URL", f"<p>{message}</p><p>{escape(url)}</p>")
                return

            result = (
                "<p>Short URL: <a href=\"/s/"
                + escape(code, quote=True)
                + "\">/s/"
                + escape(code)
                + "</a></p><p>Destination: <code>"
                + escape(url)
                + '</code></p><p><a href="/">Shorten another URL</a></p>'
            )
            self._send_page(200, "URL shortened", result)

    return RequestHandler


def create_server(host: str = "0.0.0.0", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), _handler_for(URLShortener()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args()
    if not 1 <= arguments.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    server = create_server(host=arguments.host, port=arguments.port)
    print(f"Serving on http://{arguments.host}:{arguments.port}")
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
