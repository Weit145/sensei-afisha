# Авторизация

Регистрация сразу создаёт сессию и возвращает access-токен. Каждый вход создаёт отдельную сессию: выход на одном устройстве не отключает другие.

## Ручки

| Метод и адрес | Вход | Результат |
| --- | --- | --- |
| `POST /api/auth/register` | JSON: `username`, `password` | 201, пользователь и access, refresh-cookie |
| `POST /api/auth/login` | JSON: `username`, `password` | 200, пользователь и access, refresh-cookie |
| `POST /api/auth/refresh` | Cookie, без тела | 200, пользователь и новый access, новая refresh-cookie |
| `POST /api/auth/logout` | Cookie, без тела | 204, отзыв текущей сессии и удаление cookie |
| `GET /api/auth/me` | `Authorization: Bearer <access_token>` | 200, `id`, `username`, `role` |

Ответ регистрации, входа и обновления содержит `id`, `username`, `role`, `access_token`, `token_type: "bearer"`, `expires_in` в секундах. Пароль и refresh-токен в JSON не возвращаются.

Все четыре POST-запроса требуют заголовок `X-Requested-With: XMLHttpRequest`. Это защита от CSRF: сторонняя страница не может отправить такой заголовок без разрешающего CORS preflight. Также проверяется Origin, если браузер его передал. В Swagger нужно заполнить поле `x-requested-with` значением `XMLHttpRequest`. Cookie сохраняется браузером автоматически, вручную копировать её в Swagger не требуется.

## Настройки

В локальном `.env` для HTTP установите `AUTH_COOKIE_SECURE=false`. По умолчанию включён Secure: на сервере используйте HTTPS и `AUTH_COOKIE_SECURE=true`. Настройки передаются и через Docker Compose. После изменения нужен перезапуск приложения.

По умолчанию `AUTH_COOKIE_SAMESITE=lax`, cookie — HttpOnly, без Domain, с Path `/api/auth`. Если фронтенд работает на другом origin, укажите его точно, например `CORS_ORIGINS=["http://localhost:5173"]`. Используйте один hostname: не смешивайте `localhost` и `127.0.0.1`. Список пуст, пока отдельного фронтенда нет. Звёздочка не допускается.

Если в будущем фронтенд и API окажутся на разных сайтах, понадобятся HTTPS и `AUTH_COOKIE_SAMESITE=none`; сторонние cookies могут блокироваться браузером. Пока менять эту настройку не нужно. За reverse proxy передавайте корректные Host и схему HTTPS; доверяйте forwarded-заголовкам только от своего proxy.

Access живёт `ACCESS_TOKEN_EXPIRE_MINUTES` (по умолчанию 30 минут), сессия и refresh — `REFRESH_TOKEN_EXPIRE_DAYS` (30 дней с момента входа, без продления абсолютного срока). Секрет JWT должен быть случайным и храниться только в локальном окружении, не в репозитории. В `.env.example` он оставлен пустым: сгенерируйте свой командой `openssl rand -hex 32` и задайте `JWT_SECRET_KEY` в `.env`. Ранее опубликованный пример ключа использовать нельзя; если он уже используется, замените его (все выданные токены станут недействительными).

## Подключение фронтенда

```javascript
const response = await fetch("/api/auth/login", {
  method: "POST",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
  },
  body: JSON.stringify({ username, password }),
});
if (!response.ok) throw new Error("Не удалось войти");
const { access_token } = await response.json();
```

Access держите в памяти, отправляйте как Bearer. После перезагрузки страницы получите его через `/refresh` с `credentials: "include"` и тем же защитным заголовком. HttpOnly-cookie нельзя читать из JavaScript — это ожидаемо. При 401 от `/refresh` нужен новый вход; не запускайте бесконечные повторные запросы.

Refresh одноразовый: успешное обновление заменяет его. Повторное использование старого refresh отзывает только связанную с ним сессию. Обновления нужно выполнять последовательно, включая несколько вкладок одного браузера (например, координировать через Web Locks / BroadcastChannel). Вкладки разделяют cookie; разные устройства и браузеры имеют отдельные сессии. Если отправить два обновления одновременно со старой cookie, одно пройдёт, второе отзовёт эту сессию. При потере ответа обновления может потребоваться повторный вход.

В БД хранится только SHA-256 хеш refresh. Проверка access дополнительно проверяет активность сессии и актуальную роль пользователя в БД, поэтому logout сразу запрещает новые запросы этой сессии. Уже выполняющийся запрос logout не отменяет.

## Запуск и проверка

Перед запуском новой версии примените миграцию: `poetry run alembic upgrade head`. Она добавляет `user_sessions`. Старые access-токены без идентификатора сессии перестанут приниматься — войдите заново. Docker Compose применяет миграции через сервис `migrate`.

Интеграционные проверки: `RUN_AUTH_DB_TESTS=1 poetry run python -m unittest discover -s tests -p test_auth.py -v`. Нужен PostgreSQL из `DATABASE_URL` с правом CREATE DATABASE. Проверки создают отдельные временные базы с префиксом `codex_auth_test_` и удаляют только их; таблицы основной базы не меняются.

Ограничения базовой версии: нет ограничения частоты попыток входа, восстановления пароля, списка устройств и фоновой очистки истёкших сессий. До публичного запуска добавьте rate limiting на вход и регистрацию.
