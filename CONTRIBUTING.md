# Contributing to Talentra

Thank you for contributing to Talentra! This guide outlines our development workflow, coding standards, and architectural invariants.

---

## 1. Development Principles

1. **Rule of Single Source of Truth**: All documentation changes must be made directly to the canonical files in `docs/`. Never create redundant stage reports or duplicate specification files.
2. **Preserve Database Immutability**: Financial transactions, wallet ledgers, candidate profile downloads, and security audit logs are strictly append-only. Never attempt to remove or bypass the PostgreSQL immutability triggers.
3. **Multi-Tenant Isolation**: Every query accessing tenant resources must be explicitly filtered by `organisation_id`. Cross-tenant data leakage is treated as a critical security vulnerability.
4. **No Secret Leakage**: Never commit credentials, `.env` files, or private keys to Git. Keep credentials strictly in local `.env` files.

---

## 2. Branching & Commit Conventions

### 2.1. Branch Naming
- Features: `feature/<short-description>` (e.g., `feature/candidate-blocking-ui`)
- Bug Fixes: `fix/<short-description>` (e.g., `fix/theme-toggle-contrast`)
- Documentation: `docs/<short-description>` (e.g., `docs/api-contracts-update`)
- Refactoring: `refactor/<short-description>` (e.g., `refactor/auth-service-di`)

### 2.2. Commit Messages (Conventional Commits)
Use clear, imperative commit messages prefixed with an appropriate type:
```text
feat: add candidate blocking management in profile portal
fix: resolve caret display bug in text-entry inputs
docs: update PostgreSQL exclusion constraint runbook
test: add vitest suite for employer mandate submissions
chore: prune obsolete dev dependencies
```

---

## 3. Code Quality & Standards

### 3.1. Frontend (Next.js / TypeScript)
- Strict TypeScript: No `any` types; all API responses and component props must be explicitly typed.
- Styling: Tailwind CSS classes mapped to theme tokens; no hardcoded hex color codes in UI components.
- Native Input Fidelity: Text carets must be preserved in `<input>` and `<textarea>` elements via `caret-primary`.
- Validation commands before submitting:
  ```bash
  cd frontend
  npm run typecheck
  npm run test
  npm run build
  ```

### 3.2. Backend (FastAPI / Python)
- Python 3.11+ type hints on all function parameters and return values.
- Pydantic models for request/response serialization.
- SQLAlchemy 2.x 2.0-style statements (`select(...)`, `insert(...)`).
- Validation commands:
  ```powershell
  .\.venv\Scripts\pytest -v tests/test_health.py
  .\.venv\Scripts\python.exe backend/app/verify_schema.py
  ```

---

## 4. Pull Request Checklist

Before submitting a Pull Request, verify:
- [ ] Code compiles and passes all TypeScript checks (`npm run typecheck`).
- [ ] All 154 frontend Vitest tests pass (`npm run test`).
- [ ] Backend tests and schema verifications pass.
- [ ] No temporary files, debug statements, or secrets are committed.
- [ ] Corresponding canonical documentation in `docs/` has been updated.
- [ ] PR description clearly explains the changes and references any related issue.
