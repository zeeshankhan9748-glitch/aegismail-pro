# AegisMail Pro API

FastAPI backend scaffold for Phase 1.

## Layers
- `domain`: SQLAlchemy entities and core domain concepts
- `application`: security, schemas, and use-case helpers
- `infrastructure`: database, logging, and seed utilities
- `interfaces`: HTTP routers

## Local commands
```bash
pip install -e .[dev,test]
alembic upgrade head
uvicorn app.main:app --reload
pytest
```
