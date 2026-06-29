# World Cup 2026 Office Pool — Website Version (Round of 32)

This is your prediction pool, turned into a real website. No Excel needed.

**This is an updated version** — it now matches the Round of 32 format (single
score prediction + penalty shootout pick, with the corrected scoring rules)
and includes a read-only Group Stage history page.

This README is Step 1 of 2: **testing it on your own laptop** so you can see it
and approve it before we put it online for your colleagues. Step 2 (putting it
online for everyone) comes after.

---

## What's new in this version

- **Round of 32 predictions**: one score box (covers normal + extra time) plus
  a penalty shootout pick dropdown — matching the Excel sheet exactly
- **Scoring**: 2 pts for correct winner/draw call, 3 pts for exact score,
  2 pts for correct penalty pick (max 7 pts per match)
- **Group Stage tab**: a read-only history page showing the final group stage
  standings and all 72 match results — no new predictions taken here, it's
  just for reference

---

## What's in this folder

- `app.py` — runs the website
- `database.py` / `scoring.py` — the logic (filing cabinet + calculator)
- `pool.db` — database pre-loaded with your 15 players, 16 Round of 32
  matches, and the complete Group Stage history
- `templates/` — the visual pages
- `requirements.txt` — software needed (just Flask)

---

## Part 1: Install Python (skip if already done)

If you installed Python for the earlier version, skip to Part 2.

1. Go to **python.org/downloads** → Download Python → run the installer
2. Check **"Add Python to PATH"** during install
3. Verify: open Command Prompt, type `python --version`

---

## Part 2: Open this folder in Command Prompt

Type `cd ` (with a space), drag this folder into the window, press Enter.

---

## Part 3: Install Flask (skip if already done for the earlier version)

```
pip install -r requirements.txt
```

---

## Part 4: Start the website

```
python app.py
```

Leave this window open. Look for:
```
Running on http://127.0.0.1:5000
```

---

## Part 5: Look at it in your browser

Go to:
```
http://127.0.0.1:5000
```

You should see the Round of 32 leaderboard. Click **"My Predictions"** to try
entering a score and penalty pick. Click **"Group Stage"** to see the final
standings from the group stage as a read-only reference.

---

## To stop the website

Click into the Command Prompt window and press `Ctrl + C`.

---

## What to check before we go further

- [ ] Does the Round of 32 leaderboard show all 15 players?
- [ ] Can you enter a score AND a penalty pick for a match, and save it?
- [ ] Does the Group Stage tab correctly show Maria in 1st with 38 points?
- [ ] Does it look OK on your phone too?

Once you've checked this, let me know and we'll move to **Step 2: putting
it online** so your colleagues can use it from anywhere.
