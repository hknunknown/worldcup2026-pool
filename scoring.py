"""
SCORING LOGIC - ROUND OF 32
============================
Final rules (matching the Excel sheet exactly):

  Did the match end in a draw (before penalties)?
    - YES -> +2 points if the participant ALSO predicted a draw (any draw score, not necessarily exact)
    - NO  -> +2 points if the participant predicted the correct winning team

  +3 points if the participant's predicted score is EXACT (regardless of win/draw)

  +2 points if the match went to penalties AND the participant correctly
  picked the shootout winner. This is the ONLY way to score penalty-related
  points - there's no separate "winner via penalties" bonus, since that
  would double-count the same correct guess.

  Maximum possible per match: 7 points
    (2 for correct draw-call + 3 for exact score + 2 for correct penalty pick)
"""

from database import get_connection


def calculate_r32_points(pred_home, pred_away, pen_pick, actual_home, actual_away, pen_winner):
    """
    Returns (total_points, breakdown_dict) for one match, or (None, None) if not yet scoreable.
    breakdown_dict has keys: winner_pts, exact_pts, penalty_pts
    """
    if actual_home is None or actual_away is None:
        return None, None

    went_to_pens = pen_winner is not None and pen_winner != ""

    winner_pts = 0
    exact_pts = 0
    penalty_pts = 0

    has_pred = pred_home is not None and pred_away is not None

    if has_pred:
        actual_is_draw = (actual_home == actual_away)
        pred_is_draw = (pred_home == pred_away)

        if actual_is_draw:
            # Correctly called a draw - any draw score counts, not just exact
            if pred_is_draw:
                winner_pts = 2
        else:
            # Someone won outright (no draw) - judge by predicted winner direction
            pred_diff = pred_home - pred_away
            actual_diff = actual_home - actual_away
            if (pred_diff > 0) == (actual_diff > 0):
                winner_pts = 2

        if pred_home == actual_home and pred_away == actual_away:
            exact_pts = 3

    if went_to_pens and pen_pick:
        if pen_pick == pen_winner:
            penalty_pts = 2

    total = winner_pts + exact_pts + penalty_pts
    return total, {"winner_pts": winner_pts, "exact_pts": exact_pts, "penalty_pts": penalty_pts}


def get_r32_leaderboard():
    """Builds the Round of 32 leaderboard with full breakdown columns."""
    conn = get_connection()
    cur = conn.cursor()

    players = cur.execute("SELECT id, name FROM players ORDER BY name").fetchall()
    matches = {m["num"]: m for m in cur.execute("SELECT * FROM r32_matches").fetchall()}

    leaderboard = []
    for player in players:
        preds = cur.execute(
            "SELECT * FROM r32_predictions WHERE player_id = ?", (player["id"],)
        ).fetchall()

        total_points = 0
        correct_results = 0
        exact_scores = 0
        winner_pts_total = 0
        exact_pts_total = 0
        penalty_pts_total = 0

        for p in preds:
            m = matches.get(p["match_num"])
            if not m:
                continue
            total, breakdown = calculate_r32_points(
                p["pred_home"], p["pred_away"], p["pen_pick"],
                m["home_goals"], m["away_goals"], m["pen_winner"]
            )
            if total is None:
                continue
            total_points += total
            winner_pts_total += breakdown["winner_pts"]
            exact_pts_total += breakdown["exact_pts"]
            penalty_pts_total += breakdown["penalty_pts"]
            if breakdown["winner_pts"] > 0:
                correct_results += 1
            if breakdown["exact_pts"] == 3:
                exact_scores += 1

        leaderboard.append({
            "name": player["name"],
            "total_points": total_points,
            "correct_results": correct_results,
            "exact_scores": exact_scores,
            "winner_pts": winner_pts_total,
            "exact_pts": exact_pts_total,
            "penalty_pts": penalty_pts_total,
        })

    conn.close()

    leaderboard.sort(key=lambda x: (-x["total_points"], -x["exact_scores"], -x["correct_results"], x["name"]))
    for i, row in enumerate(leaderboard, 1):
        row["rank"] = i

    return leaderboard


def get_r32_player_predictions(player_name):
    """Returns all R32 matches plus this player's predictions for the prediction page."""
    conn = get_connection()
    cur = conn.cursor()

    player = cur.execute("SELECT id FROM players WHERE name = ?", (player_name,)).fetchone()
    if not player:
        conn.close()
        return None

    matches = cur.execute("SELECT * FROM r32_matches ORDER BY num").fetchall()
    preds = {p["match_num"]: p for p in cur.execute(
        "SELECT * FROM r32_predictions WHERE player_id = ?", (player["id"],)
    ).fetchall()}

    result = []
    for m in matches:
        p = preds.get(m["num"])
        total, breakdown = (None, None)
        if p:
            total, breakdown = calculate_r32_points(
                p["pred_home"], p["pred_away"], p["pen_pick"],
                m["home_goals"], m["away_goals"], m["pen_winner"]
            )
        result.append({
            "num": m["num"],
            "date": m["date"],
            "time": m["time"],
            "home": m["home"],
            "away": m["away"],
            "actual_home": m["home_goals"],
            "actual_away": m["away_goals"],
            "actual_pen_winner": m["pen_winner"],
            "pred_home": p["pred_home"] if p else None,
            "pred_away": p["pred_away"] if p else None,
            "pen_pick": p["pen_pick"] if p else None,
            "points": total,
        })

    conn.close()
    return result


def save_r32_prediction(player_name, match_num, pred_home, pred_away, pen_pick):
    """Saves (or updates) one player's R32 prediction. Blocks edits once the match has a result."""
    conn = get_connection()
    cur = conn.cursor()

    player = cur.execute("SELECT id FROM players WHERE name = ?", (player_name,)).fetchone()
    if not player:
        conn.close()
        return False, "Player not found"

    match = cur.execute("SELECT * FROM r32_matches WHERE num = ?", (match_num,)).fetchone()
    if not match:
        conn.close()
        return False, "Match not found"
    if match["home_goals"] is not None:
        conn.close()
        return False, "This match has already started - predictions are locked"

    cur.execute("""
        INSERT INTO r32_predictions (player_id, match_num, pred_home, pred_away, pen_pick)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(player_id, match_num) DO UPDATE SET
            pred_home = excluded.pred_home,
            pred_away = excluded.pred_away,
            pen_pick = excluded.pen_pick
    """, (player["id"], match_num, pred_home, pred_away, pen_pick))

    conn.commit()
    conn.close()
    return True, "Saved"


def get_all_players():
    conn = get_connection()
    players = [row["name"] for row in conn.execute("SELECT name FROM players ORDER BY name").fetchall()]
    conn.close()
    return players


def get_r32_team_names():
    """Returns sorted list of unique team names appearing in R32 - used for the penalty-pick dropdown."""
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT home AS team FROM r32_matches UNION SELECT DISTINCT away AS team FROM r32_matches").fetchall()
    conn.close()
    return sorted(set(r["team"] for r in rows))


# ── Group Stage (read-only history) ──────────────────────────────────────────

def get_group_stage_history():
    """Returns the group stage matches (with results) and the final leaderboard snapshot."""
    conn = get_connection()
    cur = conn.cursor()

    matches = cur.execute("SELECT * FROM group_matches ORDER BY num").fetchall()
    leaderboard = cur.execute("SELECT * FROM group_leaderboard_final").fetchall()

    conn.close()
    return {
        "matches": [dict(m) for m in matches],
        "leaderboard": [dict(r) for r in leaderboard],
    }
