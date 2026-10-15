# sensei-afisha

[Бэкенд обсуждений концертов: API, локальный пример и проверки](docs/discussion.md).
[Афиша: API и примеры запросов](docs/afisha.md).
[Изображения афиш: загрузка и выдача](docs/img.md).
[Площадки: API и примеры запросов](docs/venue.md).

## Запуск через Docker

Создайте `.env` из примера и задайте в нём `JWT_SECRET_KEY` (например, с помощью `openssl rand -hex 32`):

```sh
cp .env.example .env
```

Впишите сгенерированное значение после `JWT_SECRET_KEY=`, затем запустите:

```sh
make up
```

API доступно на `http://localhost:8080`. При запуске Compose дожидается готовности PostgreSQL, применяет миграции Alembic и запускает API. Данные PostgreSQL хранятся в Docker volume.

Настройки портов и базы можно задать в `.env` по образцу `.env.example`. `DATABASE_URL` из примера предназначен для запуска приложения на хосте; внутри Compose адрес базы собирается из `POSTGRES_*` и имени сервиса `db`.

```sh
make logs                           # логи сервисов
make migrate                        # применить миграции вручную
make revision MESSAGE="add events"  # создать ревизию по изменениям моделей
make down                           # остановить сервисы, сохранив данные
make delete                         # остановить сервисы и удалить данные БД
```

Первая ревизия создаёт таблицу `users`. Для локального запуска Alembic нужен доступный PostgreSQL и подходящий `DATABASE_URL`, затем можно выполнить `alembic upgrade head`.
