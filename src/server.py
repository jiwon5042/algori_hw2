"""HTTP interface for the in-memory URL shortener."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from urllib.parse import parse_qs, urlsplit

from src.hash_table import HashTable, HashTableBackend
from src.linear_probing import LinearProbingHashTable
from src.shortener import URLShortener


MAX_FORM_BYTES = 16_384


def _render_page(title: str, content: str) -> bytes:
    document = (
        "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
        f"<title>{escape(title)}</title>"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<style>body{font:16px sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem}"
        "input{width:min(100%,36rem);padding:.5rem}button{padding:.5rem}"
        "code,pre{overflow-wrap:anywhere}.bucket{padding:.75rem 0;border-bottom:1px solid #ddd}"
        ".chain{display:flex;align-items:center;gap:.5rem;overflow-x:auto;padding:.5rem 0}"
        ".chain-node{border:1px solid #aaa;border-radius:.35rem;padding:.75rem;min-width:16rem}"
        ".chain-arrow{font-size:1.5rem;font-weight:bold}.empty{color:#666}"
        ".probe-path{font-size:.9rem;color:#555}</style>"
        f"<h1>{escape(title)}</h1>{content}</html>"
    )
    return document.encode("utf-8")


def _render_table(
    title: str,
    table: HashTable[str] | LinearProbingHashTable[str],
    urls_are_keys: bool,
) -> str:
    buckets = table.buckets
    content = [
        f"<h2>{escape(title)}</h2>",
        f"<p>Last lookup: {table.last_probes} nodes examined</p>",
        "<ol class=\"buckets\">",
    ]

    def render_node(key: str, value: str) -> str:
        url = key if urls_are_keys else value
        code = value if urls_are_keys else key
        calculated_index, steps = table.explain_hash(key)
        previous = 0
        calculations = []
        for position, (character, step) in enumerate(zip(key, steps), start=1):
            calculations.append(
                f"<li>h{position} = (31 * {previous} + ord(U+{ord(character):04X})) "
                f"mod {table.capacity} = {step}</li>"
            )
            previous = step
        if not calculations:
            calculations.append("<li>The empty key hashes to 0.</li>")
        trace = (
            f"<details><summary>Horner hash: bucket {calculated_index}</summary>"
            f"<ol>{''.join(calculations)}</ol></details>"
        )
        return (
            '<div class="chain-node">'
            f"<p><strong>URL key:</strong> <code>{escape(url)}</code></p>"
            f"<p><strong>Short code:</strong> <code>{escape(code)}</code></p>"
            f'<p><strong>Short link:</strong> <a href="/s/{escape(code, quote=True)}">'
            f"/s/{escape(code)}</a></p>"
            f"{trace}</div>"
        )

    for index, head in enumerate(buckets):
        if isinstance(table, LinearProbingHashTable):
            if head is None:
                bucket_contents = '<span class="empty">empty</span>'
            elif head.deleted:
                bucket_contents = '<span class="empty">deleted tombstone</span>'
            else:
                path = " -> ".join(str(value) for value in table.probe_path(head.key))
                bucket_contents = (
                    render_node(head.key, str(head.value))
                    + f'<p class="probe-path">probed cells: {escape(path)}</p>'
                )
            content.append(
                f'<li class="bucket">Cell {index}'
                f'<div class="chain">{bucket_contents}</div></li>'
            )
            continue

        entries = []
        node = head
        while node is not None:
            entries.append(render_node(node.key, str(node.value)))
            node = node.next
        bucket_contents = (
            '<span class="empty">empty</span>'
            if not entries
            else '<span class="chain-arrow" aria-hidden="true">&rarr;</span>'.join(entries)
        )
        content.append(
            f'<li class="bucket">Bucket {index}'
            f'<div class="chain">{bucket_contents}</div></li>'
        )
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
                strategy = (
                    "linear probing"
                    if isinstance(shortener.by_url, LinearProbingHashTable)
                    else "separate chaining"
                )
                tables = (
                    f"<p>Selected strategy: {strategy}</p>"
                    + _render_table("URLs to codes", shortener.by_url, urls_are_keys=True)
                    + _render_table("Codes to URLs", shortener.by_code, urls_are_keys=False)
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


def create_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    hash_table_class: type[HashTableBackend[str]] = HashTable,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        (host, port),
        _handler_for(URLShortener(hash_table_class=hash_table_class)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--table", choices=("chaining", "linear"), default="chaining")
    arguments = parser.parse_args()
    if not 1 <= arguments.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    if arguments.table == "linear":
        hash_table_class = LinearProbingHashTable
    else:
        hash_table_class = HashTable
    server = create_server(
        host=arguments.host,
        port=arguments.port,
        hash_table_class=hash_table_class,
    )
    print(f"Serving on http://{arguments.host}:{arguments.port}")
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
