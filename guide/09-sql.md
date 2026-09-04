# SQL для сверки оспаривания КИ

Шаг «найти в ПО и решить: подтвердить или править». В задачу писать `keyPart` / `keyDZ` / УИД / вывод по каждому пункту письма.

Доска: группа Bitrix **437** «Оспаривание КИ».  
База по умолчанию: `CZ_NewCP`. Титул выгрузок — `CZ_BKI`. Наши запросы в бюро — `CZ_KI`.

Комментарии живут в **чате задачи** (`im.dialog.messages.get` по `chatId`), не в `task.commentitem`.  
Вложения — `UF_TASK_WEBDAV_FILES` и файлы в чате. DML выгрузок (статусы 13/21/23, `KI_BKI_PrepareData`) сюда не копировать.

Различай тип задачи:

| Тип в заголовке | Что делать |
| --- | --- |
| ОСПАРИВАНИЕ | сверка ПО ↔ письмо бюро, оф. ответ / удаление запроса |
| Корректировка | чужой ДУЛ/паспорт/ИНН в файле CHP/0OA/FCH — не этот набор SELECT, править выгрузку |
| ОСПАРИВАНИЕ (возврат) / разделение КИ | файл разделения, не обычный `@answer` |
| ТЕСТ | не клиентский пакет |

Организации: `keyOH` / `@org` / `Sett.keySett`: **1** Саммит, **4** ЦВ, **5** ПКО «Доброзайм», **6** ДЗБР.

Бюро `SprAll1.keyS=224` (`Partner_BKI.typeBKI`): **1** НБКИ, **2** Эквифакс, **3** ОКБ, **4** ККИ, **6** ССП НБКИ, **7** КредИнфо. Не путать с `BKI.ContestationAnswerGet.@creditBureau`: 1 НБКИ, 2 Эквифакс/Скоринг, 3 ОКБ.

---

## 0. Разбор карточки Bitrix

Строка «Данные:»: `keyPart - ФИО (ПД:…) / (keyDZ) - Nomer_дата_сумма / uid`.

Пункт письма (после данных) выбирает запросы ниже:

| Формулировка | Раздел |
| --- | --- |
| заявка / факт оформления / мошенничество | 4 + договор |
| запросы / удалить запрос / ССП запрос | 8; ССП — `typeBKI=6` |
| просрочка / платежи / исполнено в срок | 3 |
| статус / параметры договора / задолженность / кредит | 4а |
| продажа / цессия / «договора нет в бюро» | 2 |
| банкрот | 5 |
| ФИО | 6 |
| адрес регистрации | 7 |
| договор | 2 + 4а |

Всегда начинай с поиска (п.1), даже если `keyPart`/`keyDZ` уже в описании — сверь УИД и организацию.

---

## 1. Поиск клиента — `BKI.ContestationDataSearch`

Параметр **`@parameterList`**, не `@json`. JSON — массив объектов. Часть полей может быть пустой.

```sql
DECLARE @parameterList nvarchar(max) = N''

EXEC BKI.ContestationDataSearch
  @parameterList = @parameterList
```

`identifier`: **1** ФИО, **2** дата запроса (`DogovorCred.datAnket`), **3** дата рождения, **4** ПД 10 цифр (серия 4 + номер 6), **5** сумма займа, **6** УИД (`UuidBegin` + контрольный разряд), **7** номер договора (`DogovorCred.Nomer`).

На стенде ХП черновая (нет `#IdentifierList`, лишние отладочные SELECT, `dbo.#ForAppeal`). Если падает — ищи вручную по `keyPart`/`keyDZ`/`Nomer`/`UuidBegin` из карточки.

---

## 2. Продажа / ПКО / цессия

Поиск последней продажи по договору

```sql
SELECT ds.keyDS, ds.keyDZ, ds.dat1, ds.dat2, ds.keyOH_Sell, ds.keyCA, c.NameCA, ds.datCancel
FROM dbo.Dogovor_Sell AS ds
WHERE ds.keyDZ = (/* keyDZ */)
ORDER BY ds.dat1 DESC
```

`keyOH_Sell`: 1 Саммит, 4 ЦВ, 5 ПКО, 6 ДЗБР (есть и редкие 12/13). Цепочка — по `dat1`. `datCancel` — отмена продажи. Комментарии вида «договор продан», «в ОКБ/ЭКВИ договора нет» — сначала этот запрос, не только статус в `DogovorCred`.

---

## 3. График и платежи (просрочка)

`DatPlat` — дата платежа по графику, `DatPlatFact` = факт / дата фактической оплаты, может отличаться от `DatPlat`

```sql
SELECT DatNachisl, DatPlat, DatPlatFact, SumOD, SumPrc
FROM dbo.Dogovor_GP
WHERE keyDZ = /* keyDZ */
ORDER BY DatPlat;

'MemberPay2' - все платежи по клиенту, 'vid=3' - именно платеж

SELECT mp.vid, v.NameSpr, mp.DatPlat, mp.Plateg, mp.Credit, mp.CreditOst
FROM dbo.MemberPay2 mp
WHERE mp.keyDZ = /* keyDZ */
  AND mp.vid = 3
  AND mp.Plateg > 0
ORDER BY mp.DatPlat, mp.keyP
```

Клиент пишет «исполнено в срок», а `DatPlatFact` позже `DatPlat` — в ответе подтверждать просрочку по ПО.

---

## 4. Заявка / факт оформления / анкета

`keyRec` = `keyDZ`. `Podpis = -1` — есть ЭП.

```sql
SELECT FileName, vidDoc, Podpis, DateDoc, keyRec, ForDel
FROM dbo.AppFiles
WHERE keyRec = /* keyDZ */
ORDER BY DateDoc;
```

Статус 4 / 11 / 18 сам по себе не повод исключать заявку. Подпись есть или заявка перешла в договор (`datSign` / статус 2, 3, 5, 35) — не исключать: «правомерна / перешла в договор» или «оформлена, анкета подписана».

### 4а. Карточка договора (статус, даты, сумма, УИД)

```sql
SELECT dc.keyPart, dc.keyDZ, dc.Nomer, dc.Status, sz.StatName,
       dc.datAnket, dc.dat, dc.datSign, dc.datClose, dc.SumCred,
       LOWER(CONCAT(da.UuidBegin, N'-', da.ctrlRaz)) AS uid
FROM dbo.DogovorCred dc
LEFT JOIN dbo.sprStatusZ sz ON sz.ID = dc.Status
LEFT JOIN dbo.Dogovor_Anket da ON da.keyDZ = dc.keyDZ
WHERE dc.keyDZ = /* keyDZ */;
```

«Задолженность» / «кредит» — плюс п.3. «Параметры договора» — этот SELECT, не только график.

---

## 5. Банкротство

```sql
SELECT keyB, keyPart, TypeBnk, DatEFRSB, DatEndR, NomDela, DeloEnd, DatPrizn, Prim
FROM dbo.Bankrot
WHERE keyPart = /* keyPart */;
```

---

## 6. ФИО (история)

```sql
SELECT keyFIO, nam1, nam2, nam3, FIO, DataB, datCh
FROM dbo.Partner_FIO
WHERE keyPart = /* keyPart */
ORDER BY keyFIO DESC

SELECT FN_Surname, FN_Name, FN_Middlename, FN_DateB
FROM dbo.Partner_Edit_FullName
WHERE keyPart = /* keyPart */
ORDER BY keyPEF DESC
```

---

## 7. Адрес регистрации

`Partner_Edit_Address.TypeAddress`: ориентир **2** прописка / регистрация, **3** проживание; `ForDel=0`.

```sql
SELECT TypeAddress, IndexNum, Region, District, City, Street, House, Housing, Structure, Apartment, DateReg, ForDel, dtCrt
FROM dbo.Partner_Edit_Address
WHERE keyPart = /* keyPart */ AND ISNULL(ForDel, 0) = 0
ORDER BY dtCrt DESC
```

---

## 8. Запросы, которые мы слали в бюро

```sql
SELECT pb.keyPB, pb.keyDZ, pb.keyOH, pb.requestTime, pb.typeBKI, b.NameSpr AS Bureau, pb.isError, pb.channel
FROM CZ_KI.dbo.Partner_BKI pb
LEFT JOIN cz_newCP.dbo.SprAll1 b ON b.keyS = 224 AND b.nom = pb.typeBKI
WHERE pb.keyPart = /* keyPart */
-- AND pb.typeBKI = 1   -- сузить: 1 НБКИ, 2 Эквифакс, 3 ОКБ, 6 ССП НБКИ, 7 КредИнфо
ORDER BY pb.requestTime;
```

Письмо просит удалить запрос, строки нет — всё равно слать файл удаления (для НБКИ — п.9 и `BKI.ContestationXmlCreate`). «ССП запрос» — смотри `typeBKI=6`, не обычный НБКИ=1.

---

## 10. Шапка официального ответа

Не скрипт `docs/Ответы+на+оспаривания.sql` (в репозитории его нет). Рабочая ХП:

```sql
EXEC BKI.ContestationAnswerGet
  @organizationId = 1,          -- 1 Саммит, 4 ЦВ, 5 ПКО, 6 ДЗБР
  @creditBureau   = 1,          -- 1 НБКИ, 2 Эквифакс, 3 ОКБ
  @mailNumber     = N'ИСХ///…',
  @dateMail       = N'30.12.2025',
  @FIO            = N'…',
  @answer         = N'…',
  @needSelect     = 1;
```

Два адресата в пакете — два прогона (`@organizationId` 1 и 5), два файла. КредИнфо (`typeBKI=7`) этой ХП не покрыт — отдельный канал, в комментариях часто «ответа от КредитИнфо нет».
