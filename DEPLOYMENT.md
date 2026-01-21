# Deployment Guide - Make Your App Live

## Quick Deploy Options

### Option 1: Render.com (Recommended - Free & Easy)

**Step 1: Prepare Your Code**
- ✅ All files are ready (Procfile, render.yaml created)
- ✅ Requirements.txt includes gunicorn

**Step 2: Deploy to Render**

1. **Sign up at Render.com**
   - Go to https://render.com
   - Sign up with GitHub (easiest way)

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `Bigpre12/nba-edge-finder`
   - Render will auto-detect it's a Python app

3. **Configure Settings**
   - **Name:** `nba-edge-finder` (or your choice)
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Root Directory:** (leave empty)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free (or paid for better performance)

4. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for first deployment
   - Your app will be live at: `https://nba-edge-finder.onrender.com`

5. **Add Custom Domain (Optional)**
   - Go to Settings → Custom Domains
   - Add your domain (e.g., `nbaoracle.com`)
   - Update DNS records as instructed
   - SSL certificate is automatic

---

### Option 2: Railway.app (Alternative)

1. **Sign up at Railway.app**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Deploy**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `nba-edge-finder`
   - Railway auto-detects Python and deploys

3. **Get URL**
   - Your app: `https://your-app-name.railway.app`
   - Free tier includes $5 credit/month

---

### Option 3: Fly.io (Good for Global Performance)

1. **Install Fly CLI**
   ```powershell
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login and Deploy**
   ```powershell
   fly auth login
   fly launch
   fly deploy
   ```

---

## Domain Setup (Optional but Recommended)

### Buy a Domain

**Best Options:**
- **Cloudflare Registrar:** ~$8-10/year (cheapest)
- **Namecheap:** ~$10-15/year
- **Google Domains:** ~$12/year

**Domain Suggestions:**
- `nbaoracle.com`
- `theoracleedge.com`
- `nbaedgefinder.com`
- `oracleprops.com`

### Connect Domain to Render

1. **In Render Dashboard:**
   - Go to your service → Settings → Custom Domains
   - Click "Add Custom Domain"
   - Enter your domain (e.g., `nbaoracle.com`)

2. **Update DNS (at your domain registrar):**
   - Add CNAME record:
     - **Name:** `@` or `www`
     - **Value:** `your-app.onrender.com`
   - Or A record (if provided by Render)

3. **Wait for SSL:**
   - Render automatically provisions SSL certificate
   - Takes 5-10 minutes

---

## Post-Deployment Checklist

- [ ] App loads at your URL
- [ ] All features work (edge detection, streaks, etc.)
- [ ] API endpoints respond correctly
- [ ] Custom domain works (if added)
- [ ] SSL certificate is active (https://)
- [ ] Auto-refresh works
- [ ] No errors in logs

---

## Environment Variables (If Needed)

If you need to add environment variables later:

**In Render:**
- Settings → Environment → Add Environment Variable

**Common ones:**
- `FLASK_ENV=production`
- `PYTHON_VERSION=3.11.0`

---

## Updating Your Live App

After making changes:

```powershell
# Commit changes
git add .
git commit -m "Update description"
git push

# Render/Railway auto-deploys from GitHub
# Or manually trigger redeploy in dashboard
```

---

## Troubleshooting

**App won't start:**
- Check logs in Render dashboard
- Verify `gunicorn` is in requirements.txt
- Ensure `Procfile` exists

**API errors:**
- NBA API has rate limits - may need delays
- Check internet connectivity from server

**Domain not working:**
- Verify DNS records are correct
- Wait 24-48 hours for DNS propagation
- Check SSL certificate status

---

## Cost Estimate

**Free Tier (Render):**
- Free SSL
- Free subdomain
- 750 hours/month (enough for always-on)
- Sleeps after 15 min inactivity (free tier)

**Paid Tier (Render):**
- $7/month: Always on, no sleep
- Better performance
- More resources

**Domain:**
- $8-15/year (one-time purchase)

---

## Quick Start (5 Minutes)

1. Push latest code to GitHub (already done ✅)
2. Sign up at Render.com
3. Connect GitHub repo
4. Click "Deploy"
5. Wait 5-10 minutes
6. Your app is live! 🎉

**Your app will be at:** `https://nba-edge-finder.onrender.com`
