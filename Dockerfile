FROM python:3.12-slim

WORKDIR /

RUN pip install --no-cache-dir fastapi fastapi aiohttp uvicorn pydantic requests schedule

COPY . .

EXPOSE 80 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]