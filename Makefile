PROJECT_NAME ?= dcmgate
VERSION = $(shell python3 setup.py --version | tr '+' '-')
PROJECT_NAMESPACE ?= alvassin
REGISTRY_IMAGE ?= $(PROJECT_NAMESPACE)/$(PROJECT_NAME)

all:
	@echo "make docker_dev     - Сборка Докера для дева"
	@echo "make add	- импортировать из requirements.txt в poetry"
	@echo "make migrate	- Применение миграций(изменение состояния БД)"
	@echo "make run	- запуск"
#	@echo "make coverage	- Получить % покрытия тестами"
	@exit 0



migrate:
	dbmate -d vims_code/db/migrations/ up
run:
	poetry run run_server
add:
	poetry add `cat requirements.txt`
docker_dev:
	docker-compose -f docker-compose-dev.yaml up --build

build:
	pip install poetry
	poetry install

