"""
MAIN APP (v2 - Round of 32 + Group Stage History)
===================================================
Run this file to start the website: python app.py
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import init_db, seed_initial_data
from scoring import (
    get_r32_leaderboard, get_r32_player_predictions, save_r32_prediction,
    get_all_players, get_group_stage_history, get_r32_fixtures,
    update_r32_result, get_r32_match, update_r32_team_name
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "commissioner2026")

init_db()
seed_initial_data()


@app.route("/")
def home():
    return redirect(url_for("leaderboard"))


@app.route("/leaderboard")
def leaderboard():
    board = get_r32_leaderboard()
    return render_template("leaderboard.html", leaderboard=board, active_page="leaderboard")


@app.route("/predict")
def select_player():
    players = get_all_players()
    return render_template("select_player.html", players=players, active_page="predict")


@app.route("/predict/<player_name>", methods=["GET", "POST"])
def predict(player_name):
    players = get_all_players()
    if player_name not in players:
        flash("Player not found.", "error")
        return redirect(url_for("select_player"))

    if request.method == "POST":
        saved, skipped = 0, 0
        matches = get_r32_player_predictions(player_name)
        for m in matches:
            if m["actual_home"] is not None:
                continue  # match locked, ignore any submitted value

            home_val = request.form.get(f"home_{m['num']}", "").strip()
            away_val = request.form.get(f"away_{m['num']}", "").strip()
            pen_val = request.form.get(f"pen_{m['num']}", "").strip()

            if home_val == "" and away_val == "" and pen_val == "":
                continue

            try:
                home_int = int(home_val) if home_val != "" else None
                away_int = int(away_val) if away_val != "" else None
            except ValueError:
                skipped += 1
                continue

            pen_pick = pen_val if pen_val != "" else None

            ok, _ = save_r32_prediction(player_name, m["num"], home_int, away_int, pen_pick)
            if ok:
                saved += 1
            else:
                skipped += 1

        if saved:
            flash(f"Saved {saved} prediction(s)!", "success")
        if skipped:
            flash(f"{skipped} prediction(s) could not be saved (match may have already started).", "error")
        return redirect(url_for("predict", player_name=player_name))

    matches = get_r32_player_predictions(player_name)
    return render_template("predict.html", player_name=player_name, matches=matches, active_page="predict")


@app.route("/group-stage")
def group_history():
    data = get_group_stage_history()
    return render_template(
        "group_history.html",
        matches=data["matches"],
        leaderboard=data["leaderboard"],
        active_page="history",
    )


@app.route("/fixtures")
def fixtures():
    matches = get_r32_fixtures()
    return render_template("fixtures.html", matches=matches, active_page="fixtures")


@app.route("/admin/clear", methods=["POST"])
def admin_clear():
    if not session.get("admin_authed"):
        return redirect(url_for("admin"))

    match_num = int(request.form.get("match_num"))
    update_r32_result(match_num, None, None, None)
    flash(f"✓ Match #{match_num} result cleared.", "success")
    return redirect(url_for("admin"))


@app.route("/admin", methods=["GET", "POST"])
def admin():
    authed = session.get("admin_authed", False)

    if request.method == "POST" and not authed:
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_authed"] = True
            authed = True
            flash("Welcome, Commissioner!", "success")
        else:
            flash("Wrong password.", "error")
            return render_template("admin.html", authed=False, matches=[])

    matches = get_r32_fixtures()
    return render_template("admin.html", authed=authed, matches=matches, active_page="admin")


@app.route("/admin/result", methods=["POST"])
def admin_result():
    if not session.get("admin_authed"):
        return redirect(url_for("admin"))

    match_num = int(request.form.get("match_num"))
    home_goals = request.form.get("home_goals", "").strip()
    away_goals = request.form.get("away_goals", "").strip()
    pen_winner = request.form.get("pen_winner", "").strip()

    if home_goals == "" or away_goals == "":
        flash(f"Match #{match_num}: please enter both home and away goals.", "error")
        return redirect(url_for("admin"))

    try:
        hg = int(home_goals)
        ag = int(away_goals)
    except ValueError:
        flash(f"Match #{match_num}: goals must be numbers.", "error")
        return redirect(url_for("admin"))

    update_r32_result(match_num, hg, ag, pen_winner if pen_winner else None)

    match = get_r32_match(match_num)
    flash(f"✓ Match #{match_num} ({match['home']} {hg}–{ag} {match['away']}) saved!", "success")
    return redirect(url_for("admin"))


@app.route("/admin/team", methods=["POST"])
def admin_team():
    if not session.get("admin_authed"):
        return redirect(url_for("admin"))

    match_num = int(request.form.get("match_num"))
    home = request.form.get("home", "").strip()
    away = request.form.get("away", "").strip()

    update_r32_team_name(match_num, home=home or None, away=away or None)
    flash(f"✓ Match #{match_num} team names updated.", "success")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
