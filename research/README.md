# Research / корпус

Выгрузки, встречи и скрипты сбора. **Не** на горячем пути решения задачи — см. [AGENTS.md](../AGENTS.md).

| Файл | Назначение |
|------|------------|
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
