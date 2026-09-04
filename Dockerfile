# Build the wheels in one stage, ship only what runs in the next.
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt requirements-api.txt requirements-db.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip wheel --no-cache-dir --wheel-dir /wheels \
      -r requirements-api.txt -r requirements-db.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EVERTRACK_DATABASE_URL=""

RUN useradd --create-home --uid 10001 evertrack

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*.whl \
 && rm -rf /wheels

# Only what the service needs: the domain layer, the API, and the migrations.
COPY --chown=evertrack:evertrack core/ ./core/
COPY --chown=evertrack:evertrack api/ ./api/
COPY --chown=evertrack:evertrack migrations/ ./migrations/
COPY --chown=evertrack:evertrack scripts/ ./scripts/

USER evertrack
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
