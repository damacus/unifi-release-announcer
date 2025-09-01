FROM python:3.13-slim as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN pip install uv
COPY pyproject.toml uv.lock ./

RUN uv pip install --system --no-cache -r pyproject.toml

COPY . .

FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /app /app

CMD ["python", "main.py"]
