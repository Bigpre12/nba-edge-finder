# GitHub Setup Guide

## Step 1: Install Git (if not installed)

1. Download Git for Windows: https://git-scm.com/download/win
2. Install with default settings
3. Restart your terminal/PowerShell after installation

## Step 2: Verify Git Installation

Open PowerShell and run:
```powershell
git --version
```

## Step 3: Configure Git (First Time Only)

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step 4: Initialize Git Repository

Navigate to your project folder and run:

```powershell
cd "C:\Users\preio\OneDrive\Documents\Untitled\nba_engine"
git init
```

## Step 5: Add All Files

```powershell
git add .
```

## Step 6: Create Initial Commit

```powershell
git commit -m "Initial commit: NBA Edge Finder - The Oracle"
```

## Step 7: Create GitHub Repository

1. Go to https://github.com
2. Click the "+" icon in the top right
3. Select "New repository"
4. Name it: `nba-edge-finder` (or your preferred name)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 8: Add Remote and Push

GitHub will show you commands. Use these (replace YOUR_USERNAME with your GitHub username):

```powershell
git remote add origin https://github.com/YOUR_USERNAME/nba-edge-finder.git
git branch -M main
git push -u origin main
```

If prompted for credentials:
- Username: Your GitHub username
- Password: Use a **Personal Access Token** (not your GitHub password)
  - Go to GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
  - Generate new token with `repo` scope
  - Use that token as your password

## Step 9: Future Updates

After making changes:

```powershell
git add .
git commit -m "Description of changes"
git push
```

## Alternative: Using GitHub Desktop

If you prefer a GUI:
1. Download GitHub Desktop: https://desktop.github.com/
2. Sign in with your GitHub account
3. File > Add Local Repository
4. Select your project folder
5. Publish repository to GitHub
