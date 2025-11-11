FROM python:3.11-slim AS base

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml README.md config.example.yaml ./
COPY src ./src
COPY scripts ./scripts

ENV EMP_DATABASE__URL=postgresql+psycopg2://empathy:empathy@db:5432/empathy
ENV EMP_STORAGE__DATA_DIR=/data
ENV EMP_STORAGE__TRANSCRIPTS_DIR=/data/transcripts

RUN python -m compileall src

CMD ["uvicorn", "project_empathy.main:app", "--host", "0.0.0.0", "--port", "8000"]
