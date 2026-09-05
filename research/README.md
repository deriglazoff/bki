# Research / корпус

Выгрузки, встречи и скрипты сбора. **Не** на горячем пути решения задачи — см. [AGENTS.md](../AGENTS.md).

| Файл | Назначение |
|------|------------|
| `ishod-formulations.md` | Каталог формулировок Исх: НБКИ по `task-pdfs/` (678 писем); ОКБ/Скоринг Бюро по `run/` |
| `extract_zz_udalenie_zaprosov.py` | Строгий substring-поиск фраз ЗЗ «Удаление запросов КИ» в Исх (`task-pdfs/`, `run/`) |
| `zz-udalenie-zaprosov-tasks.txt` | task_id, любая из фраз (включая короткое «правомерность запроса») |
| `zz-udalenie-zaprosov-tasks-specific.txt` | task_id без попаданий только из штампа «правомерность запроса» |
| `zz-udalenie-zaprosov-hits.csv` | строки совпадений: задача, корпус, вид файла, фраза, путь |
| `miteng.md` | Заметки планёрки по автоматизации |
| `osparivanie-2026-tasks.csv` | Выгрузка задач 2026 |
| `osparivanie-2026-comments.csv` | Выгрузка комментариев 2026 |
| `download_task_pdfs.py` | Скачать PDF вложений задач в `../task-pdfs/` |
| `ocr_task_pdfs.py` | OCR / извлечение текста из PDF |
| `create_test_tasks.py` | Создать тестовые задачи Bitrix из папок PDF |

Пересборка каталогов в `complex-cases/`:

```text
python complex-cases/rebuild_from_csv.py
```
