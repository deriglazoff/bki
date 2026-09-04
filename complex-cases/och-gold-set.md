# Эталонные ОЧ-треды (регрессия правил)

Источник: \och-gold-set.json\, 40 завершённых задач.

Использование: каждое правило из [och-card.md](och-card.md) должно попадать хотя бы в один кейс ветки; при изменении правила прогнать ветку и сверить expected action.

## Состав по веткам

| Ветка | Кол-во | Ожидаемое правило |
|-------|--------|-------------------|
| Пересечение с банкротством (тег ОЧ) (\bankrot_cross\) | 6 | R2 escalate_B |
| Продажа в ПКО (\pko\) | 8 | R3 или R4 (сверка продажи) |
| Закрытие договора (\zakryt\) | 8 | R4 если бюро расходятся; R3 если сходятся |
| Корректировка / выгрузка (\korrektirovka\) | 10 | R4 draft_correction |
| Просрочка (\prosrochka\) | 4 | R5 → R3/R4 |
| Корректно во всех бюро (\korrektno\) | 4 | R3 draft_refusal |

## Корректно во всех бюро

| task_id | labels | title |
|---------|--------|-------|
| [476101](https://resultforyou.ru/workgroups/group/437/tasks/task/view/476101/) | korrektno | ОСПАРИВАНИЕ НБКИ  МФК "Саммит" 3911177 - Уразбахтина Гульшат Олеговна |
| [476148](https://resultforyou.ru/workgroups/group/437/tasks/task/view/476148/) | korrektno | ОСПАРИВАНИЕ Экви Саммит 5908953 - Отраднова Ирина Геннадьевна |
| [480171](https://resultforyou.ru/workgroups/group/437/tasks/task/view/480171/) | korrektno | ОСПАРИВАНИЕ ЭКВИ МФК "Саммит" 5995018 Мовчан Юлия Николаевна |
| [482709](https://resultforyou.ru/workgroups/group/437/tasks/task/view/482709/) | korrektno | ОСПАРИВАНИЕ НБКИ Саммит 5310575 - Камардина Ирина Владимировна |

## Корректировка / выгрузка

| task_id | labels | title |
|---------|--------|-------|
| [490738](https://resultforyou.ru/workgroups/group/437/tasks/task/view/490738/) | korrektno, korrektirovka, prosrochka | ОСПАРИВАНИЕ ЭКВИ САММИТ  3219189 Отрезов |
| [490042](https://resultforyou.ru/workgroups/group/437/tasks/task/view/490042/) | korrektirovka, prosrochka | ОСПАРИВАНИЕ ОКБ Саммит 3219189 - Отрезов Николай Сергеевич |
| [459926](https://resultforyou.ru/workgroups/group/437/tasks/task/view/459926/) | korrektno, korrektirovka, prosrochka | ОСПАРИВАНИЕ НБКИ МФК "Саммит" 4228023 - Куприянова Наталия Владимировн |
| [457634](https://resultforyou.ru/workgroups/group/437/tasks/task/view/457634/) | korrektno, korrektirovka, prosrochka | ОСПАРИВАНИЕ НБКИ Саммит 4273399 Палкина Анастасия Никитовна |
| [465968](https://resultforyou.ru/workgroups/group/437/tasks/task/view/465968/) | korrektno, korrektirovka, prosrochka | ОСПАРИВАНИЕ ОКБ МФК "Саммит" 2876010 - Матусевич Максим Александрович |
| [492813](https://resultforyou.ru/workgroups/group/437/tasks/task/view/492813/) | korrektirovka, prosrochka | ОСПАРИВАНИЕ ОКБ МФК "Саммит" 4621313 - Макарова Елизавета Ефимовна |
| [456902](https://resultforyou.ru/workgroups/group/437/tasks/task/view/456902/) | korrektno, korrektirovka | ОСПАРИВАНИЕ ОКБ Саммит 1900909 Ионин Дмитрий Евгеньевич |
| [457059](https://resultforyou.ru/workgroups/group/437/tasks/task/view/457059/) | korrektno, korrektirovka | ОСПАРИВАНИЕ Эквифакс - МФК "Саммит" 2194155 - Захаров Виктор Михайлови |
| [459318](https://resultforyou.ru/workgroups/group/437/tasks/task/view/459318/) | korrektno, korrektirovka, prosrochka | ОСПАРИВАНИЕ ОКБ САММИТ 3489092 Костенков Виталий Игоревич |
| [454061](https://resultforyou.ru/workgroups/group/437/tasks/task/view/454061/) | korrektno, korrektirovka | ОСПАРИВАНИЕ НБКИ МФК "Саммит" 1436258 - Докучалов Александр Викторович |

## Продажа в ПКО

| task_id | labels | title |
|---------|--------|-------|
| [480155](https://resultforyou.ru/workgroups/group/437/tasks/task/view/480155/) | pko | ОСПАРИВАНИЕ ОКБ МФК "Саммит" 3920121 Гусев Николай Анатольевич |
| [479569](https://resultforyou.ru/workgroups/group/437/tasks/task/view/479569/) | korrektirovka, pko, zakryt | ОСПАРИВАНИЕ  НБКИ   МКК ДЗБР  1324508 - Мелихова Мария Сергеевна |
| [447270](https://resultforyou.ru/workgroups/group/437/tasks/task/view/447270/) | korrektirovka, pko, zakryt | ОСПАРИВАНИЕ ОКБ Саммит 1350977 Саберова Сания Садековна |
| [468663](https://resultforyou.ru/workgroups/group/437/tasks/task/view/468663/) | korrektno, korrektirovka, pko, zakryt | ОСПАРИВАНИЕ ОКБ - ПКО «Доброзайм» 3705987 - Налётов Владимир Максимови |
| [469805](https://resultforyou.ru/workgroups/group/437/tasks/task/view/469805/) | korrektno, korrektirovka, pko, zakryt | ОСПАРИВАНИЕ НБКИ САММИТ 2414463 Кондрашова Надежда Алексеевна |
| [468134](https://resultforyou.ru/workgroups/group/437/tasks/task/view/468134/) | korrektno, pko, prosrochka | ОСПАРИВАНИЕ ОКБ - МФК "Саммит" 4812532 - Дудкин Павел Сергеевич |
| [484606](https://resultforyou.ru/workgroups/group/437/tasks/task/view/484606/) | korrektirovka, pko, prosrochka | ОСПАРИВАНИЕ ОКБ  МФК "Саммит" 1240255 - Ильин Алексей Владимирович |
| [492587](https://resultforyou.ru/workgroups/group/437/tasks/task/view/492587/) | korrektirovka, pko, prosrochka | ОСПАРИВАНИЕ ОКБ МФК "Саммит" 4919003 - Офицеров Артем Николаевич |

## Просрочка

| task_id | labels | title |
|---------|--------|-------|
| [487257](https://resultforyou.ru/workgroups/group/437/tasks/task/view/487257/) | korrektno, prosrochka | ОСПАРИВАНИЕ Эквифакс МФК "Саммит" 2957659 - Фаткуллин Марат Наильевич |
| [490740](https://resultforyou.ru/workgroups/group/437/tasks/task/view/490740/) | korrektno, prosrochka | ОСПАРИВАНИЕ ОКБ МФК "Саммит" 4845913 - Севостьянова Анастасия Викторов |
| [449315](https://resultforyou.ru/workgroups/group/437/tasks/task/view/449315/) | korrektno, prosrochka | ОСПАРИВАНИЕ НБКИ ЦВ 1434339 - Кривоног Максим Сергеевич |
| [453767](https://resultforyou.ru/workgroups/group/437/tasks/task/view/453767/) | korrektno, prosrochka | ОСПАРИВАНИЕ ОКБ МФК "Саммит" 5283462 - Муравский Вадим Юрьевич |

## Закрытие договора

| task_id | labels | title |
|---------|--------|-------|
| [480580](https://resultforyou.ru/workgroups/group/437/tasks/task/view/480580/) | korrektno, korrektirovka, prosrochka, zakryt | ОСПАРИВАНИЕ ОКБ МФК "Саммит" 2876427 - Уразбаева Алина Равильевна |
| [485793](https://resultforyou.ru/workgroups/group/437/tasks/task/view/485793/) | korrektno, korrektirovka, prosrochka, zakryt | ОСПАРИВАНИЕ НБКИ "Саммит" 3672012 - Антонова Людмила Александровна |
| [492666](https://resultforyou.ru/workgroups/group/437/tasks/task/view/492666/) | korrektirovka, prosrochka, zakryt | ОСПАРИВАНИЕ ОКБ МФК "Саммит" 3186210 - Астахов Денис Николаевич |
| [472884](https://resultforyou.ru/workgroups/group/437/tasks/task/view/472884/) | korrektno, korrektirovka, prosrochka, zakryt | ОСПАРИВАНИЕ Экви Саммит 3516978 Илларионов Максим Васильевич |
| [482968](https://resultforyou.ru/workgroups/group/437/tasks/task/view/482968/) | korrektno, zakryt | ОСПАРИВАНИЕ  ОКБ   МФК Саммит   3424851 - Кирилюк Сергей Витальевич |
| [491775](https://resultforyou.ru/workgroups/group/437/tasks/task/view/491775/) | korrektirovka, prosrochka, zakryt | ОСПАРИВАНИЕ ОКБ САММИТ 2483305 Птицин |
| [492749](https://resultforyou.ru/workgroups/group/437/tasks/task/view/492749/) | korrektno, prosrochka, zakryt | ОСПАРИВАНИЕ ЭКВИ МФК "Саммит" 2483305 - Птицин Александр Геннадьевич |
| [481794](https://resultforyou.ru/workgroups/group/437/tasks/task/view/481794/) | korrektno, zakryt | ОСПАРИВАНИЕ НБКИ МФК "Саммит" 5824730 - Смирнов Алексей Дмитриевич |

## Пересечение с банкротством (тег ОЧ)

| task_id | labels | title |
|---------|--------|-------|
| [475128](https://resultforyou.ru/workgroups/group/437/tasks/task/view/475128/) | pko, zakryt, bankrot_cross | ОСПАРИВАНИЕ НБКИ ПКО 1729075 - Милошевич Антон Анатольевич |
| [482538](https://resultforyou.ru/workgroups/group/437/tasks/task/view/482538/) | korrektno, korrektirovka, prosrochka, zakryt, bankrot_cross | ОСПАРИВАНИЕ  ЭКВИ   МФК Саммит   4195176 - Володяева Елизавета Игоревн |
| [487224](https://resultforyou.ru/workgroups/group/437/tasks/task/view/487224/) | korrektno, korrektirovka, pko, prosrochka, zakryt, bankrot_cross | ОСПАРИВАНИЕ Эквифакс ПКО «Доброзайм» 4070518 - Каленова Ирина Алексеев |
| [466869](https://resultforyou.ru/workgroups/group/437/tasks/task/view/466869/) | korrektno, korrektirovka, prosrochka, bankrot_cross | ОСПАРИВАНИЕ ОКБ САММИТ 4555782 - Мавлютов Артур Ильгизович |
| [477098](https://resultforyou.ru/workgroups/group/437/tasks/task/view/477098/) | korrektno, korrektirovka, pko, prosrochka, zakryt, bankrot_cross | ОСПАРИВАНИЕ Эквифакс ПКО «Доброзайм» 3273641 - Плеханова Екатерина Вяч |
| [479850](https://resultforyou.ru/workgroups/group/437/tasks/task/view/479850/) | korrektno, korrektirovka, pko, prosrochka, zakryt, bankrot_cross | ОСПАРИВАНИЕ ОКБ ПКО «Доброзайм» 2544772 Варфоломеева Вилена Веньсовна |
