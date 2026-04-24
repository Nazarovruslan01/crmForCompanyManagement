# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- README.md with quick start, stack overview, and development commands
- Makefile with common commands (`install`, `test`, `lint`, `docker-up`, etc.)
- `.env.example` template for local development
- Pull request template
- This CHANGELOG

### Changed
- 

### Fixed
- 

### Security
- 

## [0.1.0] - 2025-04-24

### Added
- Django 5 REST backend with domain-driven apps:
  - `accounts` — custom User model with JWT auth
  - `properties` — property / unit management
  - `residents` — resident records and relations
  - `tickets` — support / maintenance tickets
  - `billing` — invoices and payment tracking
  - `staff` — employee management
  - `notifications` — system notifications
- React 19 + Vite + Tailwind CSS v4 frontend
- PostgreSQL 16 + Redis 7 + Celery 5 async task queue
- OpenAPI 3 documentation via drf-spectacular (Swagger UI + ReDoc)
- Prometheus metrics (`/metrics/`)
- Health checks (`/api/health/`, `/api/ready/`)
- GitHub Actions CI: lint, format, typecheck, migrations, tests, smoke test, Docker build, security scans
- Docker + Docker Compose setup with Gunicorn and Nginx
- Security tooling: `bandit`, `pip-audit`, `detect-secrets`, `ruff`
- Test coverage gate at 80%
