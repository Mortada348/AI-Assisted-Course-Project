# --- Stage 1: builder ---
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: runtime ---
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install dependencies collected in the builder stage.
COPY --from=builder /install /usr/local

# Copy only the application source needed at runtime.
COPY app/ ./app/

# Create a non-root user to run the app.
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
