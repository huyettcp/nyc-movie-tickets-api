
import logging
import os
from threading import Thread
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import hashlib

from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
CORS(app)

CACHE_FILE = 'cinema_cache.json'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

theaters = [
    {"name": "AMC Lincoln Square 13", "url": "https://www.movietickets.com/theater/amc-lincoln-square-13/dQ9fepfmriLGtzO"},
    {"name": "Regal Union Square ScreenX and 4DX", "url": "https://www.movietickets.com/theater/regal-union-square-screenx-and-4dx/Lrbfx2flzcP4SYq"},
    {"name": "Regal Times Square", "url": "https://www.movietickets.com/theater/regal-times-square/1K4fe6fx8fpnhxp"}
]

premium_formats = ['IMAX', 'IMAX 70MM', 'IMAX with Laser', 'IMAX with Laser 3D', 'RPX', '4DX', 'ScreenX', 
                   'RealD 3D', 'Dolby Cinema @ AMC', 'Laser at AMC', 'Digital 3D']

def generate_showtime_id(theater, movie, date, time):
    raw = f"{theater}-{movie}-{date}-{time}"
    return hashlib.md5(raw.encode()).hexdigest()

def scrape_nyc_movie_showtimes():
    logger.info("Selenium scraper started...")

    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  

    driver = uc.Chrome(options=options, use_subprocess=True)
    all_showings = []
    theater_details = []

    for theater in theaters:
        theater_name = theater["name"]
        base_url = theater["url"]

        driver.get(f"{base_url}?date={datetime.today().strftime('%Y-%m-%d')}")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        address_tag = soup.find('span', attrs={'data-qa': 'address'})
        address = address_tag.text.strip().replace("\n", " ") if address_tag else ""
        theater_details.append({"name": theater_name, "address": address})

        for i in range(7):
            date_obj = datetime.today() + timedelta(days=i)
            date_str = date_obj.strftime('%Y-%m-%d')
            url = f"{base_url}?date={date_str}"
            logger.info(f"Loading {url}")

            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'li[data-qa="movie"]'))
                )

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                movie_blocks = soup.find_all('li', attrs={'data-qa': 'movie'})
                logger.info(f"{date_str}: Found {len(movie_blocks)} movies at {theater_name}")

                for movie in movie_blocks:
                    title_tag = movie.find('span', class_='sr-text')
                    if not title_tag:
                        continue
                    title = title_tag.text.strip()

                    score_block = movie.find('div', class_=lambda x: x and 'DivMovieScores' in x)
                    rt_score = None
                    if score_block:
                        score_span = score_block.find('span', attrs={'data-qa': lambda x: x and (
                            'fresh-score' in x or 'certified_fresh-score' in x or 'rotten-score' in x
                        )})
                        if score_span:
                            rt_score = score_span.text.strip()

                    format_sections = movie.find_all('section', class_=lambda x: x and 'showtime-options' in x)

                    for variant in format_sections:
                        amenity_groups = variant.find_all('section', class_=lambda x: x and 'AmenityGroup' in x)
                        for group in amenity_groups:
                            format_tag = variant.find('div', class_=lambda x: x and 'DivVariantTitle' in x)
                            format_name = format_tag.text.strip() if format_tag else None

                            amenities = []
                            amenities_block = group.find('ul', attrs={'data-qa': 'AmenityList'})
                            if amenities_block:
                                amenities = [btn.text.strip() for btn in amenities_block.find_all('button')]

                            if not format_name or format_name == "Standard":
                                found_format = next((a for a in amenities if a in premium_formats), None)
                                format_name = found_format if found_format else "Standard"

                            showtime_links = group.find_all('a', class_=lambda x: x and 'AShowtime' in x)
                            for link in showtime_links:
                                time_text = link.find('span').text.strip()
                                relative_url = link.get('href')
                                full_url = f"https://www.movietickets.com{relative_url}"
                                show_id = generate_showtime_id(theater_name, title, date_str, time_text)

                                all_showings.append({
                                    "id": show_id,
                                    "theater": theater_name,
                                    "movie": title,
                                    "format": format_name,
                                    "amenities": amenities,
                                    "date": date_str,
                                    "rottentomatoes_score": rt_score,
                                    "time": time_text,
                                    "url": full_url
                                })

            except Exception as e:
                logger.warning(f"Error loading {url}: {e}")
                continue

    driver.quit()

    output = {
        "scraped_date": datetime.today().strftime('%Y-%m-%d'),
        "showings": all_showings,
        "theaters": theater_details
    }

    with open(CACHE_FILE, 'w') as f:
        json.dump(output, f)

    logger.info(f"Selenium scraper completed with {len(all_showings)} showings.")

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
    logger.info("Received /refresh request. Starting Selenium scraper...")

    def run_scraper():
        scrape_nyc_movie_showtimes()

    Thread(target=run_scraper).start()
    return jsonify({"status": "Refresh started. Data will update shortly."})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "NYC Movie Showtimes API is running."})

@app.route('/status', methods=['GET'])
def status_ping():
    return jsonify({"status": "Active", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

if __name__ == '__main__':
    logger.info("Running Selenium version. Visit /refresh to start scraping.")
    port = int(os.environ.get("PORT", 10000))   # Dynamic port for production
    app.run(debug=False, host='0.0.0.0', port=port)
