# Волна B: карточки фактов и guardrails

Цель: не закрыть кейс, а собрать факты, категорию, аналоги и чеклист. Сотрудник подтверждает.  
Гайды: [../guide/05-tch.md](../guide/05-tch.md), [../guide/03-bankrotstvo.md](../guide/03-bankrotstvo.md), [../guide/06-zs.md](../guide/06-zs.md). Агент: `solve-osparivanie` (без автозакрытия).

## Общая оболочка рекомендации

```json
{
  "case_type": "ТЧ|Б|ЗС",
  "confidence": 0.0,
  "facts": {},
  "analogs": [],
  "recommendation": {
    "next_step": null,
    "draft_hint": null,
    "stops": [],
    "needs_interim": false
  },
  "guardrails_fired": []
}
```

Низкий `confidence` → `next_step = "ручная разборка"`, без выдуманного решения.

---

## Карточка ТЧ (титул)

```json
{
  "case_type": "ТЧ",
  "mismatch_kind": "passport|address|fio|birthplace|glue_signal|unknown",
  "letter": { "passport": null, "address": null, "fio": null, "birthplace": null },
  "po": { "passport": null, "address": null, "fio": null, "birthplace": null, "keyPart": null },
  "bureau": {
    "NBKI": { "matches_po": null, "note": null },
    "Equifax": { "matches_po": null, "note": null },
    "OKB": { "matches_po": null, "note": null }
  },
  "linked_tasks": [],
  "new_passport_photo_in_po": null,
  "needs_interim": true
}
```

Что подсказывать:

- Расхождение письмо ↔ ПО ↔ бюро по конкретному полю.
- Связанные задачи на ту же ПД / паспорт («уже правили»).
- Нужен ли промежуточный ответ, пока ждём бюро ([interim-status.md](interim-status.md)).
- Флаг «нужна правка карточки клиента» — **без** предложения SQL.

---

## Карточка Б (банкротство)

```json
{
  "case_type": "Б",
  "bankruptcy_date": null,
  "overdue_until": null,
  "po_contract_status": null,
  "bankrot_table": { "present": null, "procedure_ended": null },
  "pko": null,
  "bureau": {
    "NBKI": { "status": null, "note": null },
    "Equifax": { "status": null, "note": null },
    "OKB": { "status": null, "note": null }
  },
  "branch": "korrektno_law|bankrot_fix|pko_bankrot|unclear"
}
```

Ветки:

| branch | Смысл | Подсказка |
|--------|-------|-----------|
| `korrektno_law` | Просрочка только до даты банкротства; в БКИ ок | Черновик: проценты стоп с даты признания, дни просрочки могут капать; сведения корректны |
| `bankrot_fix` | В Bankrot/ПО статус не ушёл в бюро | Корректировка + стоп до принятия выгрузки |
| `pko_bankrot` | Продажа + банкротство | Сверить оба факта по 3 бюро |
| `unclear` | Нет даты / противоречие | Эскалация человеку |

---

## Карточка ЗС (склейка)

```json
{
  "case_type": "ЗС",
  "subjects": [
    { "keyPart": null, "fio": null, "passport": null },
    { "keyPart": null, "fio": null, "passport": null }
  ],
  "shared_passport": null,
  "already_demerged": false,
  "linked_tasks": [],
  "bureau_letters": { "NBKI_demerge": false, "other": [] },
  "needs_interim": true
}
```

ЗС — редкий (41 кейс): только [zs-playbook.md](zs-playbook.md), не поиск «похожих» моделью как основной путь.

---

## Guardrails

Положительные цели (что система делает):

1. Показывает факты и расхождения явно.
2. Предлагает следующий шаг сотруднику.
3. Ставит стоп «не отвечать клиенту до подтверждения бюро», если была выгрузка / demerge / ждём ответ.
4. Для ТЧ/ЗС предлагает статус промежуточного ответа, когда правка ещё не подтверждена.
5. Ссылается на аналоги по **типу расхождения**, не по ФИО клиента.

Жёсткие запреты (guardrail):

| ID | Условие | Поведение |
|----|---------|-----------|
| G1 | Факты письма и ПО расходятся | Не выбирать сторону; `escalate` + чеклист сверки |
| G2 | Запрос на SQL / UPDATE Partner | Только флаг «нужна правка карточки»; SQL не генерировать |
| G3 | Нет подтверждения бюро после выгрузки | Блок официального ответа клиенту |
| G4 | Банкротство в ОЧ-карточке | `escalate_B`, не шаблон ОЧ |
| G5 | Confidence низкий | «Не уверен», без типового решения |
| G6 | ЗС | Playbook, не автозакрытие и не «удалить запросы» |
