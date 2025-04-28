# NYC Movie Tickets API

A lightweight API that provides up-to-date movie showtimes for premium theaters in NYC.  
Built with **Flask** for serving cached data and a separate **Python scraper** powered by Selenium & BeautifulSoup.

---

## Features
- **/showtimes** — Get current movie showtimes.
- **/theaters** — List of theaters with addresses.
- **/formats** — Breakdown of premium formats (IMAX, Dolby, 4DX, etc.).
- **/refresh** — Sync latest cached data from GitHub.
- **/health** — Quick status check.

---

## Project Structure

```
nyc-movie-tickets-api/
├── app.py                   # Flask API (deployed on Render)
├── scraper.py               # Scraper script (runs on VPS)
├── requirements.txt         # API dependencies
├── requirements-scraper.txt # Scraper dependencies
├── cinema_cache.json        # Cached showtimes (auto-updated)
├── .gitignore
└── README.md
```

---

## API Endpoints

| Endpoint       | Description                          |
|----------------|--------------------------------------|
| `/showtimes`   | Returns list of current showtimes    |
| `/theaters`    | Returns theater info                 |
| `/formats`     | Returns premium formats summary      |
| `/refresh`     | Pulls latest cache from GitHub       |
| `/health`      | API health check                     |
| `/status`      | API status + timestamp               |

Example:

```
GET https://nyc-movie-tickets-api.onrender.com/showtimes
```

---

## How It Works

- The **scraper** runs on a VPS, scraping showtimes from movietickets.com using undetected-chromedriver.
- Scraped data is saved to `cinema_cache.json` and pushed to GitHub.
- The **Flask API** (hosted on Render) serves this cached data via RESTful endpoints.
- `/refresh` endpoint pulls the latest JSON from GitHub if needed.

---

## Local Development

### 1. Clone the Repo
```bash
git clone https://github.com/huyettcp/nyc-movie-tickets-api.git
cd nyc-movie-tickets-api
```

---

### 2. Run the API Locally
```bash
pip install -r requirements.txt
python app.py
```
Access at: `http://localhost:10000/showtimes`

---

### 3. Run the Scraper Locally
```bash
pip install -r requirements-scraper.txt
python scraper.py
```
This will generate/update `cinema_cache.json` and push to GitHub.

---

## Deployment

- **API:** Deployed on [Render](https://render.com).
- **Scraper:** Runs on a VPS with a cron job for scheduled scraping.

---

## License
MIT License