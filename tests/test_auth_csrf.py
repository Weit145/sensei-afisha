import asyncio
import json
import unittest

from src.main import app


class AuthCsrfTests(unittest.IsolatedAsyncioTestCase):
    async def request(self, path, header=None, origin=None):
        headers = [(b"host", b"test"), (b"content-type", b"application/json")]
        if header is not None:
            headers.append((b"x-requested-with", header.encode()))
        if origin is not None:
            headers.append((b"origin", origin.encode()))
        messages = []
        sent = False

        async def receive():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": b"{}", "more_body": False}
            await asyncio.Event().wait()

        async def send(message):
            messages.append(message)

        await app(
            {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/api/auth/" + path,
                "raw_path": ("/api/auth/" + path).encode(),
                "root_path": "",
                "query_string": b"",
                "headers": headers,
                "client": ("127.0.0.1", 12345),
                "server": ("test", 80),
            },
            receive,
            send,
        )
        start = next(item for item in messages if item["type"] == "http.response.start")
        body = b"".join(
            item.get("body", b"")
            for item in messages
            if item["type"] == "http.response.body"
        )
        return start["status"], json.loads(body) if body else None

    def test_openapi_examples_do_not_set_server_default(self):
        for path in ("register", "login", "refresh", "logout"):
            with self.subTest(path=path):
                operation = app.openapi()["paths"]["/api/auth/" + path]["post"]
                parameter = next(
                    item
                    for item in operation["parameters"]
                    if item["name"] == "x-requested-with"
                )
                self.assertEqual(parameter["in"], "header")
                self.assertEqual(
                    parameter["examples"]["csrf"]["value"], "XMLHttpRequest"
                )
                self.assertIsNone(parameter["schema"].get("default"))

    async def test_missing_or_wrong_header_is_rejected(self):
        for path in ("register", "login", "refresh", "logout"):
            for header in (None, "", "wrong", "xmlhttprequest"):
                with self.subTest(path=path, header=header):
                    status, body = await self.request(path, header)
                    self.assertEqual(status, 403)
                    self.assertEqual(body["detail"]["error"]["code"], "CSRF_FAILED")

    async def test_untrusted_origin_is_rejected_with_correct_header(self):
        for path in ("register", "login", "refresh", "logout"):
            with self.subTest(path=path):
                status, body = await self.request(
                    path, "XMLHttpRequest", "https://attacker.invalid"
                )
                self.assertEqual(status, 403)
                self.assertEqual(body["detail"]["error"]["code"], "CSRF_FAILED")

    async def test_logout_accepts_explicit_header_without_cookie(self):
        for origin in (None, "http://test"):
            with self.subTest(origin=origin):
                status, body = await self.request("logout", "XMLHttpRequest", origin)
                self.assertEqual(status, 204)
                self.assertIsNone(body)


if __name__ == "__main__":
    unittest.main()
