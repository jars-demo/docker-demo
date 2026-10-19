"""The API's own tests. They run on a developer's machine and in CI, never in the image."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from server import Handler


def test_healthz_answers_ok() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/healthz"
    with urllib.request.urlopen(url) as response:
        assert json.load(response)["status"] == "ok"
    server.shutdown()
