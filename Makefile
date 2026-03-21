.PHONY: install test lint run api

install:
	pip install -e .[dev]

test:
	pytest -q

lint:
	ruff check .

run:
	python scripts/run_pipeline.py --config configs/app.example.yaml

api:
	uvicorn app.api.server:app --reload --port 8000
