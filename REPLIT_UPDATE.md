# Update Replit with Latest Changes

## Option 1: Auto-Sync from GitHub (Easiest)

If your Replit is connected to GitHub:

1. **In Replit:**
   - Click the "Version Control" icon (left sidebar)
   - Click "Pull from GitHub"
   - Or click "Sync" if it shows updates available
   - Replit will automatically pull latest changes

2. **Restart your app:**
   - Click "Stop" button
   - Click "Run" button
   - Your app will restart with latest code

---

## Option 2: Manual Pull (If Auto-Sync Doesn't Work)

1. **Open Replit Shell:**
   - Click the "Shell" tab (bottom panel)

2. **Pull from GitHub:**
   ```bash
   git pull origin main
   ```

3. **Restart your app:**
   - Stop and Run again

---

## Option 3: Re-Import from GitHub (If Connected)

1. **In Replit:**
   - Go to your Repl
   - Click "..." menu (top right)
   - Select "Sync with GitHub"
   - Or "Pull latest changes"

2. **Restart:**
   - Stop and Run

---

## What's New in This Update

✅ Auto-loads all active NBA players on first visit
✅ Shows only 70%+ probability props by default
✅ Daily 8am updates load all players automatically
✅ Line change tracking
✅ Chase list management
✅ Alternative lines tracking
✅ Edit lines anytime
✅ Toggle to show all edges

---

## After Updating

1. **First visit will:**
   - Auto-load all active players (takes 10-15 minutes first time)
   - Show only 70%+ props
   - Display player count

2. **Daily at 8am:**
   - Automatically refreshes all players
   - Updates projections
   - Filters to 70%+ props

3. **Check it works:**
   - Visit your Replit URL
   - Should see "Loaded: X active players"
   - Only 70%+ props displayed

---

## Troubleshooting

**If Replit doesn't auto-sync:**
- Use Option 2 (manual git pull)
- Or re-import from GitHub

**If app won't start:**
- Check Shell for errors
- Make sure all dependencies installed
- Try: `pip install -r requirements.txt`

**If players don't load:**
- First load takes 10-15 minutes
- Check Shell for progress
- Wait for completion

---

## Quick Update Steps

1. Open Replit
2. Click "Version Control" → "Pull from GitHub"
3. Click "Stop" then "Run"
4. Done! ✅

Your app will now auto-load all players and show only 70%+ props!
