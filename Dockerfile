FROM python:3.11-slim

ARG BUILD_DATE

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
