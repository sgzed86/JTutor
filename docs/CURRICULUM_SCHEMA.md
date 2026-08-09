# Curriculum YAML schema

Lessons are YAML files under `content/<book>/LXX.yaml` with optional `schema_version` (missing = 0).
Index files use `content/<book>/index.yaml` with `book_id`, `book_title`, and `lessons[]`.
Loaders in `backend/app/curriculum_loader.py` fill defaults for `book_id`, `book_title`, and `schema_version`.
