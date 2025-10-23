FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

RUN mkdir /logs

CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app", "--workers", "3"]