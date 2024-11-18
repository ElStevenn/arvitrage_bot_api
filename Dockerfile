FROM python:3.12-slim

RUN apt-get update && apt-get install -y nano

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80 8080

WORKDIR /src

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]