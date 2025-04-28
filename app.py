import logging
import os
import json
import hashlib
import requests
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

CACHE_FILE = 'cinema_cache.json'
GITHUB_RAW_URL = 'https://raw.githubusercontent.com/huyettcp/nyc-movie-tickets-api/main/cinema_cache.json'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_cached_data():
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Cache not found. Please trigger a refresh."}

@app.route('/showtimes', methods=['GET'])
def get_showtimes():
    data = load_cached_data()
    return jsonify(data.get("showings", []))

@app.route('/theaters', methods=['GET'])
def get_theaters():
    data = load_cached_data()
    return jsonify(data.get("theaters", []))

@app.route('/formats', methods=['GET'])
def get_formats():
    data = load_cached_data()
    formats = {}
    for show in data.get("showings", []):
        fmt = show['format']
        if fmt not in formats:
            formats[fmt] = {"theaters": set(), "showtime_ids": []}
        formats[fmt]["theaters"].add(show['theater'])
        formats[fmt]["showtime_ids"].append(show['id'])

    result = []
    for fmt, details in formats.items():
        result.append({
            "format": fmt,
            "theaters": list(details["theaters"]),
            "showtime_ids": details["showtime_ids"]
        })
    return jsonify(result)

@app.route('/refresh', methods=['GET'])
def manual_refresh():
    logger.info("Received /refresh request. Pulling latest cache from GitHub...")
    try:
        response = requests.get(GITHUB_RAW_URL)
        response.raise_for_status()
        with open(CACHE_FILE, 'w') as f:
            f.write(response.text)
        logger.info("Cache successfully updated from GitHub.")
        return jsonify({"status": "Cache refreshed from GitHub."})
    except Exception as e:
        logger.error(f"Failed to refresh cache: {e}")
        return jsonify({"status": "Failed", "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "NYC Movie Showtimes API is running."})

@app.route('/status', methods=['GET'])
def status_ping():
    return jsonify({"status": "Active", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

if __name__ == '__main__':
    logger.info("Running API-only version. Use /refresh to sync cache from GitHub.")
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
