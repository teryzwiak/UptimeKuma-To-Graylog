# Uptime Kuma Webhook to Graylog

This project is a simple **Flask webhook receiver** for monitoring systems (e.g., Uptime Kuma). It receives uptime events, parses them, and sends logs to **Graylog** using the **GELF (Graylog Extended Log Format)** protocol.

## Overview

The application exposes a single POST endpoint `/uptime` which:

1. Reads JSON payload with fields like `monitor_name`, `status`, `msg`, and `time`.
2. Parses the `msg` string for patterns such as `[MONITOR][STATUS]`.
3. Constructs a GELF log message.
4. Sends the message to a Graylog HTTP GELF endpoint, retrying on failure.

All events and errors are logged both to stdout and to `/logs/app.log`.

***

## Code details

Key settings from environment variables:

```python
GRAYLOG_URL = os.getenv("GRAYLOG_URL", "http://graylog:port/gelf")
RETRY_COUNT = int(os.getenv("RETRY_COUNT", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))
```

Logging configuration:

- Logs are written with level INFO.
- Format: `%(asctime)s [%(levelname)s] %(message)s`
- Logs saved to `/logs/app.log` and console output.

Message parsing extracts tokens enclosed in square brackets from `msg`. If pattern missing, falls back to original payload fields. Example:

```
msg = "[SERVER1][DOWN] Network unreachable"
```

creates a GELF message with `"host": "HOSTNAEM"` (note placeholder), `"short_message": "Monitor: SERVER1 - Status: DOWN"`, and log level 4 (if status is DOWN) or 6 otherwise.

The app attempts to POST the GELF message to Graylog up to `RETRY_COUNT` times, delaying `RETRY_DELAY` seconds between tries.

***

## Project Structure

```
.
├── Dockerfile
├── main.py
├── requirements.txt
└── README.md
```


***

## Running Locally

Run the Flask app directly for testing:

```bash
python3 main.py
```

Available at `http://localhost:5000/uptime`.

***

## Docker Deployment

`Dockerfile` contents:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

RUN mkdir /logs

CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app", "--workers", "3"]
```

Build Docker image:

```bash
docker build -t uptime-webhook-graylog .
```

Run Docker container:

```bash
docker run -d \
  -e GRAYLOG_URL=http://graylog:12201/gelf \
  -e RETRY_COUNT=3 \
  -e RETRY_DELAY=2 \
  -v $(pwd)/logs:/logs \
  -p 5000:5000 \
  uptime-webhook-graylog
```


***

## Example Webhook Payload

POST `/uptime` with JSON payload:

```json
{
  "monitor_name": "ISP-DC1",
  "status": "DOWN",
  "msg": "[ISP-DC1][DOWN] Ping timeout",
  "time": "2025-10-23T10:33:00Z"
}
```


***

## Success and Error Responses

- **Success:**

```json
{
  "status": "OK"
}
```

- **Error (empty data or send failure):**

```json
{
  "error": "No data"
}
```

or

```json
{
  "error": "Couldn't sent to Graylog"
}
```


***

## Logging Output Example

```
2025-10-23 13:41:11 [INFO] [OK] Log sent to Graylog: ISP-DC1 [UP]
```


***

## Notes

- Replace `"HOSTNAEM"` in `gelf_message["host"]` with your actual server hostname.
- Use environment variables to customize Graylog URL and retry behavior.
- Run with Gunicorn for production to handle multiple concurrent requests efficiently.
- Mount `/logs` directory for persistent logging in Docker.

***
