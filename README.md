# NBA Edge Finder

A web application that identifies NBA betting edges by comparing recent player performance (last 5 games average) against betting lines/projections.

## Features

- Web-based interface (no command line needed)
- Real-time edge detection on page load/refresh
- Visual display of edges with clear OVER/UNDER recommendations
- Hardcoded projections (easy to modify in code)
- API rate limiting protection
- Error handling for missing players or API failures

## Setup

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Update projections in `app.py`:
   - Edit the `MARKET_PROJECTIONS` dictionary with player names and betting lines
   - Example:
   ```python
   MARKET_PROJECTIONS = {
       "LeBron James": 24.5,
       "Kevin Durant": 26.5,
       "Stephen Curry": 28.5
   }
   ```

4. Update season if needed:
   - In `nba_engine.py`, change the default `season` parameter in `check_for_edges()` function
   - Current default: `'2023-24'`

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. The page will automatically fetch player stats and display any edges found

4. Click the "Refresh Edges" button to re-check for edges

## How It Works

1. The application fetches the last 5 games for each player in the projections
2. Calculates the average points scored over those games
3. Compares the average against the betting line
4. Identifies edges when the difference is greater than 2 points (configurable)
5. Displays recommendations: OVER if average > line, UNDER if average < line

## Configuration

### Adjusting the Edge Threshold

In `app.py`, modify the `threshold` parameter:
```python
edges = check_for_edges(MARKET_PROJECTIONS, threshold=2.0)  # Change 2.0 to your desired threshold
```

### Changing Stat Type

Currently set to points (PTS). To change, modify the `stat_type` parameter in `nba_engine.py`:
```python
def check_for_edges(projections, threshold=2.0, stat_type='PTS', season='2023-24'):
```

## Project Structure

```
nba_engine/
├── app.py                 # Main Flask application
├── nba_engine.py          # Core NBA stats fetching logic
├── templates/
│   └── index.html         # Web interface
├── static/
│   └── style.css          # Basic styling
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Notes

- The NBA API has rate limits. The application includes 1-second delays between API calls to prevent hitting limits
- Player names must match exactly as they appear in the NBA database
- The application uses the last 5 games by default, but this can be adjusted in the code
- Make sure the season string matches the format: 'YYYY-YY' (e.g., '2023-24')

## Future Enhancements

- Discord webhook integration for notifications
- Support for multiple stat types (rebounds, assists, etc.)
- Configuration file for projections
- Historical tracking of edges
- Database storage for edge history

## Troubleshooting

**No edges found:**
- Check that player names match exactly (case-sensitive)
- Verify the season is correct
- Adjust the threshold if needed
- Ensure players have played at least 5 games

**API errors:**
- Check your internet connection
- The NBA API may be temporarily unavailable
- Try again after a few minutes

**Player not found:**
- Verify the player name spelling
- Check if the player is active in the specified season
