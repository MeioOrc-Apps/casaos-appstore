FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY main.py .
RUN uv pip install --system fastapi "uvicorn[standard]" \
    && useradd --no-create-home --shell /bin/false --uid 1000 appuser \
    && mkdir -p /app/logs && chown appuser:appuser /app/logs
USER appuser
EXPOSE 8666
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8666"]
