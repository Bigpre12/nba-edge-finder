# Quick Deploy to Render - Get Your Free Domain

## Your Free URL Will Be:
**https://thepropauditor.onrender.com**

---

## Step-by-Step (5 Minutes)

### Step 1: Sign Up at Render
1. Go to **https://render.com**
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (click "Continue with GitHub")
4. Authorize Render to access your GitHub account

### Step 2: Create Web Service
1. In Render dashboard, click **"New +"** (top right)
2. Select **"Web Service"**
3. Click **"Connect account"** if needed
4. Find and select your repository: **`Bigpre12/nba-edge-finder`**
5. Click **"Connect"**

### Step 3: Configure Your Service
Fill in these settings:

- **Name:** `thepropauditor` ⭐ (This gives you thepropauditor.onrender.com)
- **Region:** Choose closest to you (US East, US West, etc.)
- **Branch:** `main`
- **Root Directory:** (leave empty)
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Plan:** Select **"Free"** (on the right side)

### Step 4: Deploy
1. Scroll down and click **"Create Web Service"**
2. Wait 5-10 minutes for first deployment
3. Watch the build logs (it will show progress)

### Step 5: Your App is Live! 🎉
Once deployment completes:
- Your app will be at: **https://thepropauditor.onrender.com**
- Free SSL certificate (automatic)
- Share this URL with anyone!

---

## Important Notes

### Free Tier Limitations:
- ⚠️ App sleeps after 15 minutes of inactivity
- ⚠️ First request after sleep takes ~30 seconds (wake up time)
- ⚠️ After that, it's fast until next sleep

### To Keep It Always Awake:
- Upgrade to **Starter Plan ($7/month)** - always on, no sleep
- Or use a free service like UptimeRobot to ping your app every 10 minutes

---

## Troubleshooting

**Build fails?**
- Check logs in Render dashboard
- Make sure `gunicorn` is in requirements.txt (✅ it is)
- Verify Python version (3.11.0)

**App won't start?**
- Check "Logs" tab in Render
- Verify Start Command: `gunicorn app:app`
- Make sure Procfile exists (✅ it does)

**Can't access after deployment?**
- Wait a few more minutes
- Check if deployment status is "Live"
- Try the URL: https://thepropauditor.onrender.com

---

## After Deployment

1. ✅ Test your app at the URL
2. ✅ Check all features work
3. ✅ Share your live app!
4. ✅ Bookmark the URL

---

## Next Steps (Optional)

**Keep App Awake (Free):**
- Sign up at https://uptimerobot.com
- Add monitor for: https://thepropauditor.onrender.com
- Set to ping every 5 minutes
- Keeps app awake 24/7 (free)

**Add Custom Domain Later:**
- Buy domain ($8-10/year)
- Add in Render Settings → Custom Domains
- Point DNS to Render

---

## You're All Set!

Once deployed, your app will be live at:
**https://thepropauditor.onrender.com**

Share it, bookmark it, use it! 🚀
