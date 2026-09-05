---
name: solve-osparivanie
description: >-
  Solves a Bitrix credit-history dispute task (оспаривание КИ) assistively:
  reads ishod/vhod, classifies, SELECTs from ПО, decides per guide, posts one
  BBCode comment with classification + ПО + decision + @answer draft. Use when
  the user pastes .../tasks/task/view/{id}/ with реши, решить, сверка, решение,
  or оспаривание (full pass, not tags-only).
---

# Решить задачу оспаривания

По URL задачи: вложения → классификация → сверка ПО (только SELECT) → решение → **один комментарий** в чат. Сотрудник потом делает ЛК бюро, выгрузку, файл удаления, XML.

Интервью не проводить. Задачу не закрывать. DML в ПО не выполнять. В бюро ничего не отправлять. Факты ПО не выдумывать.

Правила типов — только из `classification.md`. Шаги решения — из `guide/` (не копировать сюда). Глоссарий — `CONTEXT.md`. Карта — `AGENTS.md`.

Bitrix: `python scripts/b24.py` ([документация вызова](../../../scripts/b24.py)). Параметры и BBCode — UTF-8 JSON и `--file`.

## 0. ID и чат

ID из URL `.../tasks/task/view/{id}/`.

- `python scripts/b24.py call tasks.task.get --file …` с `{"taskId": ID, "select": ["*", "UF_TASK_WEBDAV_FILES"]}` → `chatId`.
- Дальше шаги 1–5. Если Исх/Вх нет — стоп после шага 1, комментарий не писать (как classify).

**Done when:** известны `taskId` и `chatId`.

## 1. Вложения Исх + Вх

Тот же съём, что у classify-osparivanie:

- `python scripts/b24.py call tasks.task.get --file …` → `ufTaskWebdavFiles` (**attached object id**).
- На каждый id: `python scripts/b24.py call disk.attachedObject.get --file …` → `NAME`, `DOWNLOAD_URL`.
- Пакет НБКИ: **txt** (`ishod` / `vhod`, имена с «исх»/«вх»); PDF — только если txt нет.
- Скачать: `python scripts/b24.py download DOWNLOAD_URL path`.
- Прочитать оба файла целиком.

**Done when:** тексты Исх и Вх есть (или явное «файлов нет» → стоп).

## 2. Классификация

Прочитать `classification.md` целиком, применить §3 (Исх + весь Вх). Детали не дублировать.

Если в чате уже есть сообщение, начинающееся с «Классификация» — запомнить его `ID` (обновить на шаге 5 вместе с полным комментарием или отдельным блоком). Не плодить второй комментарий только с тегами.

**Done when:** список тегов + подтипы с якорями в тексте файлов.

## 3. Сверка ПО (SELECT only)

Прочитать [guide/09-sql.md](../../../guide/09-sql.md). Запросы подставлять из письма (ФИО, паспорт, УИД).

Порядок:

1. Клиент → `keyPart` / актуальное ФИО (`Partner.keyFIO`) / паспорт.
2. Договоры / заявки → `keyDZ`, `UuidBegin` (= УИД без суффикса `-1`/`-4`), статусы, даты, продажа.
3. По тегам: титул (ТЧ), график/платежи/просрочка (ОЧ), `Partner_BKI` (ЗЗ), банкротство (Б), склейка/`Partner_OldPasp` (ЗС), `AppFiles.Podpis` для заявок.

### Доступ к SQL

1. **Предпочтительно:** MCP `mssql-mcp` → `execute_sql` (read-only, `cz_newcp` / cross-db `CZ_BKI`, `CZ_KI`). Конфиг: `.cursor/mcp.json`.
2. **Иначе:** `sqlcmd` на `s-po-dev.dc.centrzaimov.ru,4644`, база `cz_newcp`, Windows auth (`-E -C`), UTF-8 (`chcp 65001`, `-f 65001`).
3. **Нет доступа:** в комментарий положить готовые SELECT из §3 без выдуманных строк ПО; решение — только «нужна сверка ПО», не отказ и не «корректно».

`LIKE` по `KI_FL17.uid` не использовать. Якорь УИД — `Dogovor_Anket.UuidBegin` / `keyDZ`.

**Done when:** карточка ПО собрана **или** явный стоп «SQL недоступен» с запросами в черновике комментария.

## 4. Решение

Прочитать [guide/00-obshiy-algoritm.md](../../../guide/00-obshiy-algoritm.md) (шаги 5–8) и файлы типов по поставленным тегам:

| Тег | Гайд | Доп. указатель |
|-----|------|----------------|
| ЗЗ | [guide/04-zz.md](../../../guide/04-zz.md) | запросы удалять всегда; заявка→договор / `Podpis=-1` — не исключать |
| ОЧ | [guide/02-och.md](../../../guide/02-och.md) | правила R1–R6 [complex-cases/och-card.md](../../../complex-cases/och-card.md); формулировки — [och-gold-set](../../../complex-cases/och-gold-set.md), не поиск похожих |
| ТЧ | [guide/05-tch.md](../../../guide/05-tch.md) | карточка [assist-facts.md](../../../complex-cases/assist-facts.md) §ТЧ |
| Б | [guide/03-bankrotstvo.md](../../../guide/03-bankrotstvo.md) | [assist-facts.md](../../../complex-cases/assist-facts.md) §Б |
| ЗС | [guide/06-zs.md](../../../guide/06-zs.md) | [zs-playbook.md](../../../complex-cases/zs-playbook.md) |
| ответ | [guide/07-otvet-i-zakrytie.md](../../../guide/07-otvet-i-zakrytie.md) | два адресата → два `@org` |

Смешанный пакет — **все** контуры в одном комментарии. ЛК трёх бюро без сверки сотрудником: статус `unknown` (не имитировать из ПО).

Стопы (из гайда):

- нет клиента/договора в ПО → эскалация, не отказ;
- финал не предлагать, пока выгрузка / удаление / demerge не подтверждены;
- 3.1 не открывать, если ПО уже как в заявлении;
- заявку с подписью не исключать.

**Done when:** по каждому контуру есть действие (подтвердить / выгрузка / файл удаления / эскалация / ждать бюро) + стоп при необходимости + черновик `@answer`.

## 5. Комментарий в задачу

Один BBCode-комментарий (факты из файлов и ПО, не общие слова):

```
[B]Классификация[/B] (по classification.md)
… теги / смешанный / подтипы с якорями …

[B]ПО[/B]
keyPart=…; keyDZ / УИД / статусы / факты сверки по контурам
ЛК бюро: unknown (сверить сотруднику)

[B]Решение[/B]
• {контур}: {действие} — {якорь ПО/письма}
• Стоп: …

[B]Черновик @answer[/B]
@org=… бюро=… ИСХ=…
{текст по пунктам письма}

[B]Осталось человеку[/B]
• ЛК бюро (НБКИ/ОКБ/Экви)
• файл удаления / выгрузка / XML из docs/Ответы+на+оспаривания.sql
• теги ОфОтв или ОфОтв_Пр
```

Запись:

- Если правим существующее сообщение «Классификация» и оно станет полным решением — `python scripts/b24.py call im.message.update --file …` (`ID`, `MESSAGE`).
- Иначе / если уже есть короткий classify и нужен полный отчёт — `python scripts/b24.py call task.commentitem.add --file …` (`TASKID`, `FIELDS.POST_MESSAGE`) (один полный комментарий; старый classify не дублировать вторым «только теги»).
- `task.commentitem.getlist` / `.update` не использовать.

Проверка: `python scripts/b24.py call im.dialog.messages.get --file …` с `DIALOG_ID` = `"chat{chatId}"` — в комментарии есть теги, ПО (или стоп SQL), решение, черновик.

Если запись отклонена — отдать BBCode пользователю.

**Done when:** комментарий виден в чате (или текст отдан пользователю).
