# New Features Added

## ✅ Daily 8am Auto-Updates

**What it does:**
- Automatically runs every day at 8:00 AM
- Refreshes all projections and edges
- Tracks line changes automatically
- Pre-caches data for faster access

**How it works:**
- Uses APScheduler to run daily at 8am
- Tracks line movements (up/down)
- Logs all changes for review
- Status shown in UI: "Next update: Xh Ym"

**View Status:**
- Check status bar for next update time
- Or click "Line Management" → See daily update info

---

## ✅ Line Change Tracking

**What it tracks:**
- Every line change (previous vs current)
- Movement direction (up/down)
- Amount of movement
- Timestamp of changes

**How to use:**
1. Click "📊 Line Management" button
2. Go to "Line Changes" tab
3. See all line movements in last 24h
4. Shows: Player, Old Line → New Line, Movement amount

**Automatic:**
- Tracks changes on every refresh
- Compares today vs yesterday
- Stores history for review

---

## ✅ Chase List (What to Follow)

**What it is:**
- List of props you want to track/follow
- Add props that look good
- Track them separately from main edges

**How to use:**
1. Click "📊 Line Management"
2. Go to "Chase List" tab
3. Add props manually (via API) or from edges
4. Remove when done tracking

**API Endpoint:**
- POST `/api/chase-list` - Add to chase list
- GET `/api/chase-list` - View chase list
- DELETE `/api/chase-list` - Remove from chase list

---

## ✅ Alternative Lines Tracking

**What it tracks:**
- Different lines from different books
- Main line vs alternative lines
- Line differences
- Source of alternative line

**How to use:**
1. Click "📊 Line Management"
2. Go to "Alt Lines" tab
3. View all alternative lines tracked
4. See differences between main and alt lines

**API Endpoint:**
- POST `/api/alt-lines` - Add alternative line
- GET `/api/alt-lines` - View all alt lines

---

## ✅ Edit Lines (Even After Send-Off)

**What it does:**
- Update lines even after they've been sent off
- Track manual line changes
- Update projections on the fly

**How to use:**
1. Click "📊 Line Management"
2. Go to "Edit Lines" tab
3. Select player from dropdown
4. Enter old line and new line
5. Click "Update Line"
6. Line is updated immediately

**Features:**
- Updates projections file
- Tracks the change in history
- Refreshes edges automatically
- Works even after initial send-off

---

## 📊 Line Management Panel

**Access:**
- Click "📊 Line Management" button in controls

**Tabs:**
1. **Line Changes** - See what moved
2. **Chase List** - Props to follow
3. **Alt Lines** - Alternative lines tracked
4. **Edit Lines** - Update lines manually

---

## 🔄 How Daily Updates Work

**Schedule:**
- Runs every day at 8:00 AM
- Uses server timezone
- Can be manually triggered via API

**What happens:**
1. Reloads all projections
2. Tracks line changes (vs yesterday)
3. Refreshes edge calculations
4. Pre-caches data
5. Logs all changes

**Manual Trigger:**
- POST to `/api/trigger-update`
- Or use "Line Management" panel

---

## 📝 Files Created

- `line_tracker.py` - All line tracking logic
- `lines_history.json` - Stores line history (auto-created)
- `chase_list.json` - Stores chase list (auto-created)
- `alt_lines.json` - Stores alt lines (auto-created)

---

## 🎯 Usage Examples

### Track a Line Change:
- Happens automatically when you refresh
- View in "Line Changes" tab

### Add to Chase List:
```javascript
fetch('/api/chase-list', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        player: 'LeBron James',
        line: 24.5,
        stat_type: 'PTS',
        reason: 'Strong edge, track this'
    })
})
```

### Add Alternative Line:
```javascript
fetch('/api/alt-lines', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        player: 'LeBron James',
        main_line: 24.5,
        alt_line: 25.5,
        stat_type: 'PTS',
        source: 'PrizePicks'
    })
})
```

### Update a Line:
- Use "Edit Lines" tab in UI
- Or POST to `/api/update-line`

---

## ⚙️ Configuration

**Daily Update Time:**
- Currently: 8:00 AM
- Change in `app.py`:
  ```python
  scheduler.add_job(
      func=daily_update_job,
      trigger="cron",
      hour=8,  # Change this
      minute=0,
      ...
  )
  ```

**Timezone:**
- Uses server timezone
- For specific timezone, add `timezone` parameter to scheduler

---

## 🚀 Ready to Deploy!

All features are implemented and ready. Your app will:
- ✅ Auto-update daily at 8am
- ✅ Track all line changes
- ✅ Let you manage chase list
- ✅ Track alternative lines
- ✅ Allow line editing anytime

Deploy and it all works automatically!
