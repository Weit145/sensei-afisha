# Контакты участников

Для всех запросов нужен заголовок `Authorization: Bearer <access_token>`.

## Посмотреть контакты по ID

`GET /api/users/{user_id}/contacts`

В `user_id` передайте `user_id` из WebSocket-уведомления либо `author_id` из сообщения или отзыва.

Ответ `200 OK`:

```json
{
  "user_id": "4e036140-87f8-4e0b-b6e7-f3349c4898fc",
  "nickname": "listener_1",
  "tg_url": "https://t.me/listener_1",
  "vk_url": null
}
```

Фронтенд может показать `nickname` и ссылки на Telegram/VK. `null` означает, что контакт не указан; если обе ссылки `null`, предложите связаться в обсуждении концерта. Пароль, роль и токены в этом ответе отсутствуют. Ответ не кешируется (`Cache-Control: no-store`).

Ошибки: `401` — требуется вход, `404` — пользователь не найден, `422` — некорректный UUID.

## Свои контакты

`GET /api/auth/me/contacts` возвращает `tg_url` и `vk_url` текущего пользователя.

`PATCH /api/auth/me/contacts` изменяет только его собственные контакты. Дополнительно передайте `Content-Type: application/json` и `X-Requested-With: XMLHttpRequest`.

```json
{
  "tg_url": "https://t.me/listener_1",
  "vk_url": "https://vk.com/listener_1"
}
```

Можно передать одно поле. Пропущенные поля сохраняются, `null` или пустая строка удаляет контакт. Допустимы HTTPS-ссылки на `t.me`, `telegram.me` и `vk.com`. Сохранённые контакты доступны другим авторизованным участникам клуба по ID пользователя.
