FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY main.py entrypoint.sh ./
COPY static/ static/
RUN apt-get update && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && uv pip install --system fastapi "uvicorn[standard]" httpx \
    && useradd --no-create-home --shell /bin/false --uid 1000 appuser \
    && chmod +x /app/entrypoint.sh
EXPOSE 8666
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8666"]
