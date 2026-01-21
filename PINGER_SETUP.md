# Website Pinger Setup Guide

Keep your website active by pinging it every 13 minutes to prevent spin-down.

## Option 1: External Pinger Services (Recommended - Free)

### UptimeRobot (Free - 50 monitors)

1. Go to [https://uptimerobot.com](https://uptimerobot.com)
2. Sign up for a free account
3. Click "Add New Monitor"
4. Configure:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Your App Name
   - **URL:** `https://your-app.onrender.com/ping` (or your domain)
   - **Monitoring Interval:** 5 minutes (closest to 13)
   - **Alert Contacts:** Add your email
5. Click "Create Monitor"

**Note:** Free tier allows 5-minute intervals (closest to 13 minutes)

### cron-job.org (Free)

1. Go to [https://cron-job.org](https://cron-job.org)
2. Sign up for free account
3. Click "Create cronjob"
4. Configure:
   - **Title:** Keep App Alive
   - **Address:** `https://your-app.onrender.com/ping`
   - **Schedule:** Every 13 minutes: `*/13 * * * *`
   - **Request Method:** GET
5. Click "Create"

### EasyCron (Free - 1 job)

1. Go to [https://www.easycron.com](https://www.easycron.com)
2. Sign up for free account
3. Create new cron job:
   - **Cron Job Title:** Keep App Alive
   - **URL:** `https://your-app.onrender.com/ping`
   - **Schedule:** `*/13 * * * *` (every 13 minutes)
4. Save

---

## Option 2: Python Script (Run Locally or on Server)

### Setup

1. Install required package:
   ```bash
   pip install requests
   ```

2. Run the pinger script:
   ```bash
   python pinger.py https://your-app.onrender.com/ping
   ```

### Run Every 13 Minutes

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Keep App Alive"
4. Trigger: Daily, repeat every 13 minutes
5. Action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\pinger.py https://your-app.onrender.com/ping`
6. Save

#### Linux/Mac (Cron)

Add to crontab (`crontab -e`):
```bash
*/13 * * * * /usr/bin/python3 /path/to/pinger.py https://your-app.onrender.com/ping >> /path/to/pinger.log 2>&1
```

---

## Option 3: GitHub Actions (Free)

Create `.github/workflows/ping.yml`:

```yaml
name: Keep App Alive

on:
  schedule:
    - cron: '*/13 * * * *'  # Every 13 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Website
        run: |
          curl -f https://your-app.onrender.com/ping || exit 1
```

---

## Option 4: Internal Scheduler (If App Stays Active)

If your app doesn't spin down, you can use the internal scheduler:

The app already has a `/ping` endpoint. You can add a self-ping feature, but this only works if the app is already running.

---

## Recommended: UptimeRobot

**Why UptimeRobot?**
- ✅ Free tier (50 monitors)
- ✅ 5-minute intervals (close to 13)
- ✅ Email alerts if site goes down
- ✅ Dashboard to monitor uptime
- ✅ No server needed
- ✅ Reliable and trusted

**Setup Time:** 2 minutes

---

## Your Ping Endpoints

Your app has these endpoints ready:
- `/ping` - Simple ping (returns "pong")
- `/health` - Health check (returns JSON status)

Use either one - `/ping` is simpler and faster.

---

## Testing

Test your pinger:
```bash
curl https://your-app.onrender.com/ping
```

Should return: `pong`

---

## Notes

- **13 minutes** is chosen to be under typical 15-minute spin-down thresholds
- **5 minutes** (UptimeRobot free tier) is also fine and more frequent
- Multiple pingers won't hurt - redundancy is good
- Monitor your app's logs to confirm pings are working
