from __future__ import annotations

import http.client
import json
import time

from project_empathy.bootstrap import create_schema, seed_demo_data
from project_empathy.main import create_app
from project_empathy.runtime.server import serve_in_thread


def test_runtime_server_serves_http_requests():
    create_schema()
    seed_demo_data(skip_existing=False)
    app = create_app()

    server, thread = serve_in_thread(app)
    host, port = server.server_address
    try:
        # wait briefly for the background server to bind
        time.sleep(0.2)
        conn = http.client.HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/api/v1/restaurants/")
        response = conn.getresponse()
        payload = response.read().decode("utf-8") or "[]"
        data = json.loads(payload)

        assert response.status == 200
        assert isinstance(data, list)
        assert data, "the demo seeding should expose at least one restaurant"
        assert {"id", "name", "phone_number"}.issubset(data[0])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
