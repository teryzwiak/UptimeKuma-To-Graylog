from flask import Flask, request, jsonify
import requests
import json
import logging
import time
import os
import re

app = Flask(__name__)

GRAYLOG_URL = os.getenv("GRAYLOG_URL", "http://graylog:port/gelf")
RETRY_COUNT = int(os.getenv("RETRY_COUNT", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@app.route("/uptime", methods=["POST"])
def uptime_webhook():
    data = request.json
    if not data:
        logger.warning("Get empty load ")
        return jsonify({"error": "No data"}), 400

    monitor_name = data.get('monitor_name', 'unknown')
    status = data.get('status', 'unknown')
    msg = data.get('msg', '[POWERUP][UP]')
    event_time = data.get('time', '')

    matches = re.findall(r'\[(.*?)\]', msg)
    print(f'Matches found: {matches}')

    if len(matches) >= 2:
        monitor_name = matches[0]
        status = re.sub(r'[^\w\s]', '', matches[1])
    else:
        # fallback jeśli brak wzorca
        logger.warning(f"no msg format: {msg}")
        monitor_name = data.get('monitor_name', 'unknown')
        status = data.get('status', 'unknown')

    gelf_message = {
        "version": "1.1",
        "host": "HOSTNAEM",
        "short_message": f"Monitor: {monitor_name} - Status: {status}",
        "full_message": msg,
        "_monitor_name": monitor_name,
        "_status": status,
        "_time": event_time,
        "level": 4 if status.upper() == "DOWN" else 6
    }

    success = False
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            resp = requests.post(GRAYLOG_URL, json=gelf_message, timeout=5)
            if resp.status_code == 202:
                logger.info(f"[OK] Log sent to Graylog: {monitor_name} [{status}]")
                success = True
                break
            else:
                logger.error(f"[{attempt}/{RETRY_COUNT}] Error Graylog: {resp.status_code}")
        except Exception as e:
            logger.error(f"[{attempt}/{RETRY_COUNT}] Explicity: {e}")
        time.sleep(RETRY_DELAY)

    if success:
        return jsonify({"status": "OK"}), 200
    else:
        return jsonify({"error": "Couldn't sent to Graylog"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)