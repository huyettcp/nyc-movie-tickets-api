# NYC Movie Showtimes API

A Flask-based API that scrapes NYC premium format movie showtimes from AMC and Regal theaters. 

## 🚀 Features
- Scrapes showtimes for IMAX, Dolby Cinema, 4DX, and more.
- Caches data for fast API responses.
- Endpoints for showtimes, theaters, formats, and health checks.
- Manual and automated refresh via `/refresh`.

## 🛠️ Setup

### Local Development
1. Clone the repo.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Access at `http://localhost:10000/health`

### Production Deployment (Render Example)
- **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  gunicorn app:app --bind 0.0.0.0:$PORT
  ```

### Automate Scraping
Use a cron job to hit:
```bash
curl https://your-api-url.onrender.com/refresh
```

## 📖 API Endpoints
- `GET /health` — Check if API is running.
- `GET /refresh` — Trigger scraper.
- `GET /showtimes` — Get cached showtimes.
- `GET /theaters` — List theaters.
- `GET /formats` — List available premium formats.
- `GET /status` — Simple status ping.

## ⚡ Notes
- Scraper runs headless via Selenium + Chrome.
- Cached data stored in `cinema_cache.json`.
