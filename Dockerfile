FROM python:3.11-slim
WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY app ./app
COPY scripts ./scripts
COPY configs ./configs
RUN pip install --no-cache-dir -e .
CMD ["uvicorn", "app.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
