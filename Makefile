# ===========================================
# Bookly Project Makefile
# ===========================================

.PHONY: help
help: ## Показать справку по доступным командам
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# ===========================================
# Docker Compose
# ===========================================

.PHONY: up
up: ## Запустить все сервисы (foreground)
	docker compose up

.PHONY: up-d
up-d: ## Запустить все сервисы (background)
	docker compose up -d

.PHONY: down
down: ## Остановить все сервисы
	docker compose down

.PHONY: restart
restart: ## Перезапустить все сервисы
	docker compose restart

.PHONY: logs
logs: ## Показать логи всех сервисов
	docker compose logs -f

.PHONY: logs-backend
logs-backend: ## Показать логи backend
	docker compose logs -f backend

.PHONY: logs-frontend
logs-frontend: ## Показать логи frontend
	docker compose logs -f frontend

.PHONY: logs-nginx
logs-nginx: ## Показать логи nginx
	docker compose logs -f nginx

.PHONY: ps
ps: ## Показать статус сервисов
	docker compose ps

# ===========================================
# Backend: Миграции
# ===========================================

.PHONY: migrate
migrate: ## Применить миграции
	docker compose exec backend python manage.py migrate

.PHONY: makemigrations
makemigrations: ## Создать файл миграции
	docker compose exec backend python manage.py makemigrations

.PHONY: makemigrations-app
makemigrations-app: ## Создать миграцию для конкретного приложения (usage: make makemigrations-app app=accounts)
	docker compose exec backend python manage.py makemigrations $(app)

.PHONY: showmigrations
showmigrations: ## Показать статус миграций
	docker compose exec backend python manage.py showmigrations

.PHONY: migrate-app
migrate-app: ## Применить миграции конкретного приложения (usage: make migrate-app app=accounts)
	docker compose exec backend python manage.py migrate $(app)

# ===========================================
# Backend: Статика и данные
# ===========================================

.PHONY: collectstatic
collectstatic: ## Собрать статику backend
	docker compose exec backend python manage.py collectstatic --noinput

.PHONY: loaddata
loaddata: ## Загрузить фикстуры (usage: make loaddata file=data.json)
	docker compose exec backend python manage.py loaddata $(file)

.PHONY: dumpdata
dumpdata: ## Выгрузить данные в фикстуру (usage: make dumpdata file=data.json)
	docker compose exec backend python manage.py dumpdata --indent 2 > $(file)

.PHONY: createsuperuser
createsuperuser: ## Создать суперпользователя
	docker compose exec backend python manage.py createsuperuser

.PHONY: load-landing-content
load-landing-content: ## Загрузить контент лендинга
	docker compose exec backend python manage.py load_landing_content --force

# ===========================================
# Backend: Тесты
# ===========================================

.PHONY: test
test: ## Запустить тесты backend
	docker compose exec backend python manage.py test

.PHONY: test-app
test-app: ## Запустить тесты конкретного приложения (usage: make test-app app=accounts)
	docker compose exec backend python manage.py test $(app)

.PHONY: test-coverage
test-coverage: ## Запустить тесты с покрытием
	docker compose exec backend coverage run --source='.' manage.py test
	docker compose exec backend coverage report

.PHONY: pytest
pytest: ## Запустить pytest (если установлен)
	docker compose exec backend pytest

# ===========================================
# Backend: Прочее
# ===========================================

.PHONY: shell
shell: ## Открыть Django shell
	docker compose exec backend python manage.py shell

.PHONY: dbshell
dbshell: ## Открыть database shell
	docker compose exec backend python manage.py dbshell

.PHONY: check
check: ## Проверить код на ошибки
	docker compose exec backend python manage.py check

# ===========================================
# Frontend
# ===========================================

.PHONY: frontend-install
frontend-install: ## Установить зависимости frontend
	docker compose exec frontend pnpm install

.PHONY: frontend-dev
frontend-dev: ## Запустить frontend в режиме разработки
	docker compose exec frontend pnpm dev --host 0.0.0.0

.PHONY: frontend-build
frontend-build: ## Собрать frontend
	docker compose exec frontend pnpm build

.PHONY: frontend-lint
frontend-lint: ## Запустить линтер frontend
	docker compose exec frontend pnpm lint

.PHONY: frontend-typecheck
frontend-typecheck: ## Проверить типы frontend
	docker compose exec frontend pnpm typecheck

# ===========================================
# Development (локальный запуск без Docker)
# ===========================================

.PHONY: dev-backend
dev-backend: ## Запустить backend локально
	cd backend && python manage.py runserver

.PHONY: dev-frontend
dev-frontend: ## Запустить frontend локально
	cd frontend && pnpm dev

.PHONY: install-backend
install-backend: ## Установить зависимости backend
	cd backend && pip install -r requirements.txt

.PHONY: install-frontend
install-frontend: ## Установить зависимости frontend
	cd frontend && pnpm install

# ===========================================
# Cleanup
# ===========================================

.PHONY: clean
clean: ## Очистить временные файлы
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/.output frontend/.nuxt frontend/.cache 2>/dev/null || true

.PHONY: clean-volumes
clean-volumes: ## Удалить volumes (данные БД, redis)
	docker compose down -v

.PHONY: clean-all
clean-all: clean clean-volumes ## Полная очистка
	docker compose down --rmi all

# ===========================================
# Build
# ===========================================

.PHONY: build
build: ## Пересобрать все сервисы
	docker compose build

.PHONY: build-backend
build-backend: ## Пересобрать backend
	docker compose build --no-cache backend

.PHONY: build-frontend
build-frontend: ## Пересобрать frontend
	docker compose build --no-cache frontend

.PHONY: build-nginx
build-nginx: ## Пересобрать nginx
	docker compose build nginx
