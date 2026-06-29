"""
DATABASE SETUP (v2 - Round of 32 + Group Stage History)
=========================================================
Two kinds of data now:
  1. Round of 32 - LIVE predictions (the new format: one score + penalty pick)
  2. Group Stage - READ-ONLY history (already finished, just for reference)
"""

import sqlite3
import json
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "pool.db")


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # ── Round of 32 (live) ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS r32_matches (
            num INTEGER PRIMARY KEY,
            date TEXT,
            time TEXT,
            home TEXT,
            away TEXT,
            home_goals INTEGER,
            away_goals INTEGER,
            pen_winner TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS r32_predictions (
            player_id INTEGER NOT NULL,
            match_num INTEGER NOT NULL,
            pred_home INTEGER,
            pred_away INTEGER,
            pen_pick TEXT,
            PRIMARY KEY (player_id, match_num),
            FOREIGN KEY (player_id) REFERENCES players(id),
            FOREIGN KEY (match_num) REFERENCES r32_matches(num)
        )
    """)

    # ── Group Stage (read-only history) ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS group_matches (
            num INTEGER PRIMARY KEY,
            date TEXT,
            home TEXT,
            away TEXT,
            home_goals INTEGER,
            away_goals INTEGER,
            stage TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS group_leaderboard_final (
            rank_label TEXT,
            name TEXT,
            total_points INTEGER,
            correct_results INTEGER,
            exact_scores INTEGER
        )
    """)

    conn.commit()
    conn.close()


def seed_initial_data():
    here = os.path.dirname(__file__)
    conn = get_connection()
    cur = conn.cursor()

    # --- Players ---
    cur.execute("SELECT COUNT(*) FROM players")
    if cur.fetchone()[0] == 0:
        players = ["Mijke", "Maria", "Szymon", "Mateusz", "Souvik", "Santosh",
                   "Shubham", "Neha", "Vikash", "Aditya", "Pankaj", "Kamal",
                   "Pragin", "Drew", "Prasenjit"]
        cur.executemany("INSERT INTO players (name) VALUES (?)", [(p,) for p in players])
        print(f"Seeded {len(players)} players")

    # --- Round of 32 matches ---
    cur.execute("SELECT COUNT(*) FROM r32_matches")
    if cur.fetchone()[0] == 0:
        with open(os.path.join(here, "r32_matches.json")) as f:
            matches = json.load(f)
        for m in matches:
            cur.execute("""
                INSERT INTO r32_matches (num, date, time, home, away, home_goals, away_goals, pen_winner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (m["num"], m["date"], m["time"], m["home"], m["away"],
                  m["home_goals"], m["away_goals"], m["pen_winner"]))
        print(f"Seeded {len(matches)} Round of 32 matches")

    # --- Round of 32 predictions (if any exist already) ---
    cur.execute("SELECT COUNT(*) FROM r32_predictions")
    if cur.fetchone()[0] == 0:
        path = os.path.join(here, "r32_predictions.json")
        if os.path.exists(path):
            with open(path) as f:
                all_preds = json.load(f)
            name_to_id = {row["name"]: row["id"] for row in
                          cur.execute("SELECT id, name FROM players").fetchall()}
            count = 0
            for name, preds in all_preds.items():
                pid = name_to_id.get(name)
                if not pid:
                    continue
                for match_num, p in preds.items():
                    cur.execute("""
                        INSERT INTO r32_predictions (player_id, match_num, pred_home, pred_away, pen_pick)
                        VALUES (?, ?, ?, ?, ?)
                    """, (pid, int(match_num), p["home"], p["away"], p.get("pen_pick")))
                    count += 1
            print(f"Seeded {count} existing Round of 32 predictions")

    # --- Group stage matches (history) ---
    cur.execute("SELECT COUNT(*) FROM group_matches")
    if cur.fetchone()[0] == 0:
        path = os.path.join(here, "group_matches.json")
        if os.path.exists(path):
            with open(path) as f:
                matches = json.load(f)
            for m in matches:
                cur.execute("""
                    INSERT INTO group_matches (num, date, home, away, home_goals, away_goals, stage)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (m["num"], m["date"], m["home"], m["away"],
                      m["home_goals"], m["away_goals"], m["stage"]))
            print(f"Seeded {len(matches)} group stage matches (history)")

    # --- Group stage final leaderboard (history) ---
    cur.execute("SELECT COUNT(*) FROM group_leaderboard_final")
    if cur.fetchone()[0] == 0:
        path = os.path.join(here, "group_leaderboard.json")
        if os.path.exists(path):
            with open(path) as f:
                rows = json.load(f)
            for row in rows:
                cur.execute("""
                    INSERT INTO group_leaderboard_final (rank_label, name, total_points, correct_results, exact_scores)
                    VALUES (?, ?, ?, ?, ?)
                """, (str(row["rank"]), row["name"], row["total_points"],
                      row["correct_results"], row["exact_scores"]))
            print(f"Seeded {len(rows)} group stage final leaderboard rows (history)")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_initial_data()
    print("Database ready at:", DB_FILE)
