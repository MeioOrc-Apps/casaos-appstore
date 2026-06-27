FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY main.py .
RUN uv pip install --system fastapi "uvicorn[standard]"
EXPOSE 6666
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6666"]
