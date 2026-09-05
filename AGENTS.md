# Агент: оспаривание КИ

Цель репозитория: по URL задачи Bitrix наполнить чат так, чтобы сотрудник мог исполнить (ЛК бюро, выгрузка, файл удаления, XML), не разбирая пакет с нуля.

Assistive-контур: комментарий = классификация + сверка ПО (SELECT) + решение + черновик `@answer` + стопы.  
Не делать агентом: DML в ПО, отправку в бюро, закрытие задачи, автоответ клиенту.

## Карта источников

| Нужно | Читать |
|-------|--------|
| Глоссарий | [CONTEXT.md](CONTEXT.md) |
| Типы и подтипы, пакет НБКИ | [classification.md](classification.md) — **единственный SoT меток** |
| Общий алгоритм задачи | [guide/00-obshiy-algoritm.md](guide/00-obshiy-algoritm.md) |
| План по тегу | [guide/](guide/) (`02-och` … `06-zs`, `07-otvet-i-zakrytie`, `09-sql`) |
| Карточки / эталоны / аналоги | [complex-cases/](complex-cases/) |
| Корпус и сборщики | [research/](research/) — не на горячем пути решения |

Краткий список тегов: [type.md](type.md) (ссылка на `classification.md`).  
Маршрутизация контуров: [complex-cases/taxonomy.md](complex-cases/taxonomy.md) — не переопределяет типы.

## Скиллы

| Скилл | Когда |
|-------|--------|
| [classify-osparivanie](.cursor/skills/classify-osparivanie/SKILL.md) | Только теги/подтипы в комментарий |
| [solve-osparivanie](.cursor/skills/solve-osparivanie/SKILL.md) | Полный assistive-прогон: файлы → классификация → ПО → решение → комментарий |

## Инструменты

- Bitrix: входящий webhook REST через [`scripts/b24.py`](scripts/b24.py) (не MCP).
  Webhook: env `B24_DEFAULT_WEBHOOK`, иначе `~/.cursor/mcp.json` (`B24_DEFAULT_WEBHOOK` или заголовок `X-B24-Webhook`).
  Длинные параметры и BBCode — `--file` (UTF-8 JSON).
  Вложения: `python scripts/b24.py download DOWNLOAD_URL path`.

## SQL / ПО

- Конфиг MCP: [`.cursor/mcp.json`](.cursor/mcp.json) → сервер `mssql-mcp` (read-only, `ApplicationIntent=ReadOnly`, access-mode `restricted`).
- Бинарь проекта: `E:/repos/mcp-ms-sql/vendor/mssql-mcp/...` (соседний репозиторий). После смены mcp.json перезапустить MCP в Cursor.
- Fallback без MCP: `sqlcmd -S s-po-dev.dc.centrzaimov.ru,4644 -d cz_newcp -E -C` (см. скилл solve-osparivanie).
- Шаблоны SELECT: [guide/09-sql.md](guide/09-sql.md).

## Жёсткие стопы

- Клиент или договор не найдены в ПО → эскалация, не отказ.
- Финал не предлагать, пока выгрузка / удаление запросов / demerge не подтверждены бюро.
- Заявку с подписанной анкетой (`Podpis = -1`) или уже договором — не исключать.
- 3.1 не открывать, если актуальное ФИО/паспорт в ПО уже как в заявлении.
- ЛК трёх бюро без сверки сотрудником помечать `unknown`, не имитировать из ПО.
