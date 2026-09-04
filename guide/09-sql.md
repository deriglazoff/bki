# SQL для сверки оспаривания

SELECT-ы для шага «найти в ПО и решить: подтвердить или править».  
Писать в задачу `keyPart` / `keyDZ` / УИД / вывод по каждому пункту письма.

База по умолчанию: `cz_newCP`. Титул выгрузок — `CZ_BKI`. Наши запросы в бюро — `CZ_KI`.  
В выборках договоров: `ISNULL(ForDel, 0) <> -1`. УИД из письма = `Dogovor_Anket.UuidBegin` **без** суффикса `-1` / `-4`.  
`LIKE` по `KI_FL17.uid` не использовать — медленно; якорь — `UuidBegin` / `keyDZ`.

DML выгрузок (статусы 13/21/23, `KI_BKI_PrepareData`) — в [02-och.md](02-och.md) и [05-tch.md](05-tch.md), сюда не копировать.

## 1. Клиент по ФИО или паспорту

Серия в ПО слитно (`8012`, не `80 12`). Несколько строк `Partner_FIO` — смотреть актуальную через `Partner.keyFIO` (запрос 2).

```sql
SELECT TOP 30
  fio.keyPart, fio.keyFIO, fio.FIO, fio.nam1, fio.nam2, fio.nam3, fio.DataB,
  ped.Serial, ped.Number, ped.IssuedDate, ped.IssuedCode, ped.ForDel
FROM cz_newCP.dbo.Partner_FIO fio
LEFT JOIN cz_newCP.dbo.Partner_Edit_Documents ped
  ON ped.keyPart = fio.keyPart AND ISNULL(ped.ForDel, 0) <> -1
WHERE fio.FIO LIKE N'%Фамилия%'
   OR (ped.Serial = N'8012' AND ped.Number = N'692517')
ORDER BY fio.keyPart DESC;
```

## 2. Актуальное ФИО (не история)

История может держать старые варианты (Алиткачева / Алипкачева). В ответ и в сверку ТЧ идёт строка с `Partner.keyFIO`.

```sql
SELECT p.keyPart, p.keyFIO, fio.FIO, fio.nam1, fio.nam2, fio.nam3, fio.DataB,
       p.INN, p.SNILS
FROM cz_newCP.dbo.Partner p
JOIN cz_newCP.dbo.Partner_FIO fio ON fio.keyFIO = p.keyFIO
WHERE p.keyPart = /* keyPart */;
```

История ФИО (все записи, в т.ч. `FN_Type` 1 текущее / 2 предыдущее):

```sql
SELECT keyPEF, FN_Surname, FN_Name, FN_Middlename, FN_DateB, FN_Type, ForDel, dtCrt
FROM cz_newCP.dbo.Partner_Edit_FullName
WHERE keyPart = /* keyPart */
ORDER BY dtCrt DESC;
```

## 3. Паспорт

```sql
SELECT keyPED, Serial, Number, IssuedDate, IssuedBy, IssuedCode, ForDel
FROM cz_newCP.dbo.Partner_Edit_Documents
WHERE keyPart = /* keyPart */
ORDER BY keyPED DESC;

SELECT keyOldPasp, PS, PN, dat
FROM cz_newCP.dbo.Partner_OldPasp
WHERE keyPart = /* keyPart */;
```

Титул, который уже уходил в бюро (`CZ_BKI`): если здесь уже «как в заявлении» — 3.1 не готовить, пока ЛК не покажет иное.

```sql
SELECT DISTINCT lastName, firstName, midName
FROM CZ_BKI.dbo.KI_FL1_name WHERE keyPart = /* keyPart */;

SELECT DISTINCT idSeries, idNum, issueDate, deptCode
FROM CZ_BKI.dbo.KI_FL4_id WHERE keyPart = /* keyPart */;
```

Адрес (ТЧ FL8/FL9):

```sql
SELECT TOP 20 *
FROM cz_newCP.dbo.Partner_Edit_Address
WHERE keyPart = /* keyPart */;
```

## 4. Договоры и УИД

```sql
SELECT
  d.keyDZ, d.Nomer, d.SumCred, d.Status, st.StatName,
  d.dtDog, d.DatDog, d.DatAnket, d.datSign, d.datClose,
  da.UuidBegin, da.dt_ASP_odobr, da.ASP_cnt
FROM cz_newCP.dbo.DogovorCred d
LEFT JOIN cz_newCP.dbo.sprStatusZ st ON st.ID = d.Status
LEFT JOIN cz_newCP.dbo.Dogovor_Anket da ON da.keyDZ = d.keyDZ
WHERE d.keyPart = /* keyPart */
  AND ISNULL(d.ForDel, 0) <> -1
ORDER BY d.DatDog, d.keyDZ;
```

Поиск по УИД из письма (без суффикса):

```sql
SELECT d.keyPart, d.keyDZ, d.Nomer, d.Status, da.UuidBegin
FROM cz_newCP.dbo.Dogovor_Anket da
JOIN cz_newCP.dbo.DogovorCred d ON d.keyDZ = da.keyDZ
WHERE da.UuidBegin = '4C2F6783-6BA0-11D9-9752-418D643B662F';
```

Частые `sprStatusZ`: 2 выдан, 3 закрыт, 4 заявка отклонена, 5 закрыт с просрочкой, 11 отказался клиент, 18 автоотказ, 35 прекращён.

## 5. Продажа / ПКО

```sql
SELECT ds.keyDS, ds.keyDZ, ds.dat1, ds.dat2, ds.keyOH_Sell, ds.keyCA, c.NameCA
FROM cz_newCP.dbo.Dogovor_Sell ds
LEFT JOIN cz_newCP.dbo.sprCollector c ON c.keyCA = ds.keyCA
WHERE ds.keyDZ IN (/* keyDZ */);
```

`keyOH_Sell`: 1 Саммит, 5 ПКО «Доброзайм». Цепочка из нескольких строк — читать по `dat1`.

## 6. График и платежи (ОЧ)

`DatPlat` — срок, `DatPlatFact` = дата прекращения/продажи при непогашенном платеже.

```sql
SELECT DatNachisl, DatPlat, DatPlatFact, SumOD, SumPrc
FROM cz_newCP.dbo.Dogovor_GP
WHERE keyDZ = /* keyDZ */
ORDER BY DatPlat;

SELECT mp.vid, v.NameSpr, mp.DatPlat, mp.Plateg, mp.Credit, mp.CreditOst
FROM cz_newCP.dbo.MemberPay2 mp
LEFT JOIN cz_newCP.dbo.SprAll1 v ON v.keyS = 104 AND v.nom = mp.vid
WHERE mp.keyDZ = /* keyDZ */ AND ISNULL(mp.ForDel, 0) <> -1
ORDER BY mp.DatPlat, mp.keyP;
```

Клиент пишет «исполнено в срок», а `DatPlatFact` позже `DatPlat` — в ответе подтверждать просрочку по ПО, не заявление.

## 7. Подписанная анкета (ЗЗ)

`keyRec` = `keyDZ` заявки/договора. `Podpis = -1` — есть ЭП.

```sql
SELECT FileName, vidDoc, Podpis, DateDoc, keyRec, ForDel
FROM cz_newCP.dbo.AppFiles
WHERE keyRec = /* keyDZ */
ORDER BY DateDoc;
```

Статус 4 / 11 / 18 сам по себе не повод исключать заявку: сначала этот запрос. Подпись есть или заявка перешла в договор (`datSign` / статус 2, 3, 5, 35) — не исключать, в `@answer` «правомерна / перешла в договор» или «оформлена, анкета подписана».

## 8. Запросы, которые мы слали в бюро

```sql
SELECT pb.keyPB, pb.keyDZ, pb.requestTime, pb.typeBKI, b.NameSpr AS Bureau, pb.isError
FROM CZ_KI.dbo.Partner_BKI pb
LEFT JOIN cz_newCP.dbo.SprAll1 b ON b.keyS = 224 AND b.nom = pb.typeBKI
WHERE pb.keyPart = /* keyPart */
ORDER BY pb.requestTime;
```

Письмо просит удалить запрос, строки в таблице нет — всё равно слать файл удаления. `typeBKI` на стенде: 1 НБКИ, 2 Эквифакс, 4 ККИ (справочник `SprAll1` keyS=224).

## 9. Имя файла удаления запросов НБКИ

```sql
DECLARE @Date nvarchar(8) = FORMAT(GETDATE(), 'yyyyMMdd'),
        @Time nvarchar(6) = FORMAT(GETDATE(), 'HHmmss'),
        @keyOH int = 1;  -- 1 Саммит, 4 ЦВ, 5 ПКО, 6 ДЗБР

SELECT FORMATMESSAGE('%s_%s_%s', S.NBKI_Memb_KI, @Date, @Time)
FROM cz_newCP.dbo.Sett AS S
WHERE S.keySett = @keyOH;
```

Саммит → `WD01BB000002_…xlsx.zip.enc` на CancelCreditHistory@nbki.ru. ПКО → `ZW01RR000001_…`.

## 10. Шапка официального ответа

Полный скрипт — [`docs/Ответы+на+оспаривания.sql`](../docs/Ответы+на+оспаривания.sql). В шапке только переменные:

```sql
DECLARE @org smallint = 1,  -- 1 Саммит, 5 ПКО, 6 ДЗБР
        @creditBureau nvarchar(50) = N'АО «НБКИ»',
        -- АО «НБКИ» | АО «БКИ «Скоринг Бюро» | АО «ОКБ»
        @numberMailFromBureau nvarchar(50) = N'ИСХ///242959',
        @dateMailFromBureau nvarchar(50) = N'30.12.2025',
        @FIO nvarchar(300) = N'Сахибгареева Лилия Эриковна';
```

Два адресата в пакете — два прогона (`@org` 1 и 5), два файла. Формулы `@answer` — [07-otvet-i-zakrytie.md](07-otvet-i-zakrytie.md).
