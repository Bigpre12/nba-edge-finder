# Ultra-Light NBA Edge Finder Deployment

## Architecture Overview

```
GitHub Actions (scrape every 15 min)
        ↓
   data/*.json (committed to repo)
        ↓
    Render (serves static files + tiny FastAPI)
        ↓
    Browser (vanilla JS with caching)
```

## Files Created

| File | Purpose |
|------|---------|
| `scraper.py` | Lightweight NBA API scraper (runs in GitHub Actions) |
| `.github/workflows/scrape-data.yml` | Scheduled scraping workflow |
| `main.py` | Minimal FastAPI server (~100 lines) |
| `static/index.html` | Accessible HTML with tabs |
| `static/app.js` | Vanilla JS with AbortController + caching |
| `static/style-lite.css` | Lightweight CSS (~8KB) |
| `requirements-lite.txt` | Only 3 dependencies |
| `render-lite.yaml` | Render configuration |

## Deployment Steps

### 1. Commit all files

```bash
git add -A
git commit -m "Add ultra-light architecture"
git push
```

### 2. Run scraper manually first

Go to GitHub → Actions → "Scrape NBA Data" → "Run workflow"

This creates the initial `data/*.json` files.

### 3. Deploy to Render

**Option A: Use render-lite.yaml**
- Go to Render Dashboard
- New → Blueprint
- Connect repo, select `render-lite.yaml`

**Option B: Manual setup**
- New → Web Service
- Build Command: `pip install -r requirements-lite.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`

### 4. Verify deployment

```bash
# Health check
curl https://your-app.onrender.com/health

# API check
curl https://your-app.onrender.com/api/props
```

## Debugging Checklist

### Tabs Not Working?

1. **Open Browser DevTools (F12) → Console**
   - Look for JavaScript errors
   - Should see: "NBA Edge Finder ready"

2. **Check Network tab**
   - Click a tab
   - Should see: `GET /api/props` request
   - Status should be 200

3. **Verify data exists**
   ```bash
   curl https://your-app.onrender.com/api/props
   ```
   Should return JSON with `count > 0`

4. **Check if AbortController is canceling**
   - Rapid tab switching should show "Request aborted" in console
   - This is normal behavior

### No Data Loading?

1. **Check GitHub Actions ran**
   - Go to repo → Actions tab
   - Verify "Scrape NBA Data" workflow succeeded
   - Check `data/props.json` exists in repo

2. **Check data files exist on Render**
   ```bash
   curl https://your-app.onrender.com/data/props.json
   ```

3. **Manually trigger scrape**
   - Go to Actions → "Scrape NBA Data" → "Run workflow"

### Memory Issues?

1. **Check Render metrics**
   - Dashboard → your service → Metrics
   - Memory should be < 100MB

2. **Verify single worker**
   - Logs should show: "Started server process [X]" (only one)

### Cache Issues?

1. **Clear browser cache**
   - DevTools → Application → Clear storage

2. **Clear localStorage**
   ```javascript
   // In browser console
   localStorage.clear()
   ```

3. **Force refresh**
   - Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

## Testing Tabs Locally

```bash
# 1. Create test data
mkdir -p data
echo '{"updated":"2024-01-01T00:00:00Z","count":2,"props":[{"player":"LeBron James","id":2544,"props":{"pts":{"line":25.5,"avg":26.0,"prob":72,"pick":"OVER"},"reb":{"line":7.5,"avg":8.0,"prob":68,"pick":"OVER"},"ast":{"line":8.5,"avg":9.0,"prob":75,"pick":"OVER"}}},{"player":"Kevin Durant","id":201142,"props":{"pts":{"line":27.5,"avg":28.0,"prob":70,"pick":"OVER"},"reb":{"line":6.5,"avg":7.0,"prob":65,"pick":"OVER"},"ast":{"line":5.5,"avg":6.0,"prob":72,"pick":"OVER"}}}]}' > data/props.json

# 2. Install dependencies
pip install -r requirements-lite.txt

# 3. Run server
uvicorn main:app --reload --port 8000

# 4. Open browser
# http://localhost:8000
```

### Tab Test Checklist

- [ ] Click "Points" tab → Shows points props
- [ ] Click "Rebounds" tab → Shows rebounds props  
- [ ] Click "Assists" tab → Shows assists props
- [ ] Click "All Props" tab → Shows all stats per player
- [ ] Use keyboard: Tab to tabs, Arrow keys to navigate, Enter to select
- [ ] Change filter dropdown → Props filter correctly
- [ ] Wait 15s → Data auto-refreshes (check console)
- [ ] Rapid tab switching → No errors, requests canceled properly

## Memory Comparison

| Mode | RAM Usage | Dependencies |
|------|-----------|--------------|
| Original Flask app | 300-500MB | 20+ packages |
| Ultra-light FastAPI | 30-50MB | 3 packages |

## Rollback

To switch back to the original app:

1. Change Render start command back to:
   ```
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
   ```

2. Change requirements file to `requirements.txt`

## GitHub Actions Schedule

The scraper runs:
- Every 15 minutes (`*/15 * * * *`)
- On push to `scraper.py` or workflow file
- Manually via "Run workflow" button

To change frequency, edit `.github/workflows/scrape-data.yml`:
```yaml
schedule:
  - cron: '*/5 * * * *'   # Every 5 minutes
  - cron: '0 * * * *'     # Every hour
  - cron: '0 */6 * * *'   # Every 6 hours
```
