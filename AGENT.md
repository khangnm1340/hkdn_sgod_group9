# Project Development Instructions

## Architecture

- Frontend: React + TypeScript.
- Backend: Django + Django REST Framework.
- Database: PostgreSQL.
- File storage: Local filesystem.
- Package Manager: uv
- Version control: jujutsu(jj)

## Rules

1. Follow docs/database-and-api-spec.md.
2. Do not change API contracts without updating documentation.
3. Do not modify unrelated files.
4. Every feature must include appropriate tests.
5. Never commit uploaded datasets, generated exports, or secrets.
6. Use migrations for database schema changes.
7. Validate user input on the backend.
8. Explain architectural decisions before introducing
   new dependencies or changing existing patterns.

## Development Workflow

1. Understand the assigned issue.
2. Inspect relevant existing code.
3. Implement the smallest working change.
4. Write tests.
5. Run relevant tests and lint checks.
6. Summarize files changed and remaining limitations.
