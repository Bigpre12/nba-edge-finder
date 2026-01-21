# Free Domain Setup Guide

## Option 1: Free Subdomain (Recommended - 100% Free)

### Using Render.com Free Subdomain

When you deploy to Render, you automatically get:
- **Free URL:** `https://thepropauditor.onrender.com`
- **Free SSL Certificate**
- **Always works, no cost**

**Steps:**
1. Deploy to Render (see DEPLOYMENT.md)
2. Your app will be at: `https://thepropauditor.onrender.com`
3. That's it! Completely free.

**Pros:**
- ✅ 100% free forever
- ✅ SSL included
- ✅ Professional looking
- ✅ Easy to remember

**Cons:**
- ⚠️ Has `.onrender.com` in URL
- ⚠️ Free tier sleeps after 15 min inactivity (wakes on first request)

---

## Option 2: Free Domain Services (Use with Caution)

### Freenom (.tk, .ml, .ga, .cf domains)

**Website:** https://www.freenom.com

**How to get:**
1. Sign up at Freenom
2. Search for `thepropauditor`
3. Select `.tk`, `.ml`, `.ga`, or `.cf` extension
4. Register for free (up to 12 months)
5. Point DNS to your Render app

**Pros:**
- ✅ Actually free domain name
- ✅ No `.onrender.com` in URL

**Cons:**
- ⚠️ Some browsers block these domains
- ⚠️ Reputation issues (often used for spam)
- ⚠️ May be unreliable
- ⚠️ Need to renew yearly

**If you use Freenom:**
1. Get domain: `thepropauditor.tk` (or .ml, .ga, .cf)
2. In Freenom DNS settings, add:
   - Type: CNAME
   - Name: @
   - Target: `your-app.onrender.com`
3. In Render, add custom domain: `thepropauditor.tk`

---

## Option 3: GitHub Pages Subdomain (Free but Limited)

**Free URL:** `https://bigpre12.github.io/nba-edge-finder`

**Note:** This only works for static sites. Your Flask app needs a server, so this won't work directly. You'd need to convert to static or use a different approach.

---

## Option 4: Free Domain with Hosting Promotions

Some registrars offer free domains with hosting:
- **Namecheap:** Sometimes offers free .xyz domains
- **Google Domains:** Occasionally has promotions
- **Cloudflare:** $8-10/year (not free, but very cheap)

---

## Recommended Setup: Free Subdomain

**Best Option:** Use Render's free subdomain

1. **Deploy to Render**
   - Your app: `https://thepropauditor.onrender.com`
   - Completely free
   - Professional URL

2. **If you want shorter URL later:**
   - Buy domain for $8-10/year when ready
   - Point it to Render (free to do)

---

## Quick Setup Steps

### Step 1: Deploy to Render
1. Go to https://render.com
2. Sign up with GitHub
3. Deploy your repo
4. Name your service: `thepropauditor`
5. Your URL: `https://thepropauditor.onrender.com`

### Step 2: (Optional) Get Free Domain from Freenom
1. Go to https://www.freenom.com
2. Search: `thepropauditor`
3. Select `.tk` or `.ml` extension
4. Register (free)
5. Point DNS to Render

### Step 3: Connect Domain to Render
1. In Render dashboard → Settings → Custom Domains
2. Add: `thepropauditor.tk` (or whatever you got)
3. Update DNS in Freenom as Render instructs
4. Wait 24-48 hours for DNS propagation

---

## Cost Comparison

| Option | Cost | URL Example | Quality |
|--------|------|-------------|---------|
| Render Subdomain | **FREE** | thepropauditor.onrender.com | ⭐⭐⭐⭐ |
| Freenom .tk | **FREE** | thepropauditor.tk | ⭐⭐ |
| Cloudflare Domain | $8-10/year | thepropauditor.com | ⭐⭐⭐⭐⭐ |

---

## My Recommendation

**Start with Render's free subdomain:**
- `https://thepropauditor.onrender.com`
- 100% free
- Professional
- Easy to set up
- Upgrade to custom domain later if needed

**If you really want a custom domain for free:**
- Try Freenom (.tk, .ml, .ga, .cf)
- Be aware of limitations
- Consider it temporary until you can afford $8-10/year for a real domain

---

## Next Steps

1. Deploy to Render (get free subdomain)
2. Test your app at the free URL
3. If you want, try Freenom for free custom domain
4. Later, upgrade to paid domain ($8-10/year) when ready
