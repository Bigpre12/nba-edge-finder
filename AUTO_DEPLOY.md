# Automated Deployment Setup

## Option 1: Railway.app (CLI - Can Be Automated)

Railway has a CLI that allows automated setup. Let me set this up for you.

### Step 1: Install Railway CLI

```powershell
# Windows (PowerShell)
iwr https://railway.app/install.ps1 -useb | iex
```

### Step 2: Login to Railway

```powershell
railway login
```

### Step 3: Initialize and Deploy

```powershell
railway init
railway up
```

This will:
- Create a new Railway project
- Deploy your app automatically
- Give you a free URL like: `thepropauditor-production.up.railway.app`

---

## Option 2: Fly.io (CLI - Fully Automated)

Fly.io has excellent CLI support and can be fully automated.

### Step 1: Install Fly CLI

```powershell
# Windows PowerShell
iwr https://fly.io/install.ps1 -useb | iex
```

### Step 2: Login

```powershell
fly auth login
```

### Step 3: Launch and Deploy

```powershell
fly launch
# Follow prompts, it will auto-detect your app
fly deploy
```

Your app will be at: `https://thepropauditor.fly.dev`

---

## Option 3: PythonAnywhere (Free Tier Available)

PythonAnywhere offers free hosting for Python apps.

1. Sign up at https://www.pythonanywhere.com
2. Upload your files via web interface
3. Configure web app
4. Free URL: `yourusername.pythonanywhere.com`

---

## Option 4: Replit (Easiest - Browser Based)

Replit can import from GitHub and deploy automatically.

1. Go to https://replit.com
2. Sign up with GitHub
3. Click "Import from GitHub"
4. Enter: `Bigpre12/nba-edge-finder`
5. Replit auto-deploys
6. Free URL: `your-app-name.repl.co`

---

## Recommended: Railway CLI Setup

Railway is the best balance of:
- ✅ Free tier
- ✅ CLI automation
- ✅ Easy setup
- ✅ Good performance

Let me create the Railway setup files for you.
