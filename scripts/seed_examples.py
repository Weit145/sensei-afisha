"""Заполнить локальный API демонстрационными афишами и постерами."""

import argparse
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

POSTERS_DIR = Path(__file__).resolve().parents[1] / "frontend" / "public" / "posters"
MOSCOW_TIME = timezone(timedelta(hours=3))
VENUE = {
    "name": "Георгиевский зал (демо)",
    "city": "Москва",
    "address": "Адрес уточняется у организаторов",
}
CONCERTS = (
    {
        "title": "Демо · Бах. Искусство слышать",
        "short_description": "Орган и музыка, в которой каждый находит что-то своё.",
        "description": "Камерный вечер музыки Баха. После концерта можно поделиться впечатлениями в обсуждении.",
        "poster": "bach-organ.png",
        "age_limit": 6,
    },
    {
        "title": "Демо · Джаз при свечах",
        "short_description": "Фортепиано, контрабас и немного импровизации.",
        "description": "Вечер джазового трио в камерной атмосфере Георгиевского зала.",
        "poster": "jazz-candles.png",
        "age_limit": 12,
    },
    {
        "title": "Демо · Моцарт рядом",
        "short_description": "Струнный квартет и разговор о музыке.",
        "description": "Камерный вечер музыки Моцарта. Приходите слушать и знакомиться.",
        "poster": "mozart-quartet.png",
        "age_limit": 6,
    },
)


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    content_type: str | None = None,
) -> dict:
    headers = {"Content-Type": content_type} if content_type else {}
    request = Request(f"{base_url}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path}: HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Не удалось подключиться к {base_url}: {error.reason}") from error


def find_item(base_url: str, path: str, title: str, field: str) -> dict | None:
    page = 1
    while True:
        query = urlencode({"search": title, "page": page, "page_size": 100})
        result = request_json(base_url, f"{path}?{query}")
        for item in result["items"]:
            if item[field] == title:
                return item
        if page * 100 >= result["total"]:
            return None
        page += 1


def multipart_afisha(afisha: dict, poster: Path) -> tuple[bytes, str]:
    boundary = f"----sensei-demo-{uuid.uuid4().hex}"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="afisha"\r\n\r\n'
    ).encode()
    body += json.dumps(afisha, ensure_ascii=False).encode("utf-8")
    body += (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="images"; filename="{poster.name}"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode()
    body += poster.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def next_monday_evening() -> datetime:
    now = datetime.now(MOSCOW_TIME)
    days_until_monday = (7 - now.weekday()) % 7
    start = (now + timedelta(days=days_until_monday)).replace(
        hour=19, minute=0, second=0, microsecond=0
    )
    return start if start > now else start + timedelta(days=7)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    base_url = parser.parse_args().base_url.rstrip("/")

    for concert in CONCERTS:
        poster = POSTERS_DIR / concert["poster"]
        if not poster.is_file():
            raise FileNotFoundError(f"Постер не найден: {poster}")

    venue = find_item(base_url, "/api/venues", VENUE["name"], "name")
    if venue is None:
        venue = request_json(
            base_url,
            "/api/venues",
            method="POST",
            body=json.dumps(VENUE, ensure_ascii=False).encode("utf-8"),
            content_type="application/json",
        )
        print(f"Создана площадка: {venue['id']}")
    else:
        print(f"Площадка уже есть: {venue['id']}")

    first_date = next_monday_evening()
    for index, concert in enumerate(CONCERTS):
        title = concert["title"]
        existing = find_item(base_url, "/api/afisha", title, "title")
        if existing is not None:
            print(f"Уже есть: {title} — {existing['id']}")
            continue

        starts_at = first_date + timedelta(weeks=index)
        data = {
            "title": title,
            "short_description": concert["short_description"],
            "description": concert["description"],
            "starts_at": starts_at.isoformat(),
            "ends_at": (starts_at + timedelta(hours=2)).isoformat(),
            "venue_ids": [venue["id"]],
            "age_limit": concert["age_limit"],
        }
        body, content_type = multipart_afisha(data, POSTERS_DIR / concert["poster"])
        created = request_json(
            base_url,
            "/api/afisha",
            method="POST",
            body=body,
            content_type=content_type,
        )
        image_url = created["images"][0]["image_url"]
        print(f"Создан концерт: {title} — {created['id']} ({image_url})")


if __name__ == "__main__":
    main()
