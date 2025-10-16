from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..extensions import db
from ..models import League, Membership, Player, RosterEntry
from ..services.analysis import analyze_sit_start


roster_bp = Blueprint("roster", __name__, url_prefix="/roster")


@roster_bp.route("/<int:league_id>")
@login_required
def view(league_id: int):
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    entries = (
        RosterEntry.query.filter_by(user_id=current_user.id, league_id=league_id)
        .join(Player)
        .order_by(Player.position, Player.name)
        .all()
    )
    return render_template("roster/view.html", league_id=league_id, entries=entries)


@roster_bp.route("/<int:league_id>/add", methods=["POST"]) 
@login_required
def add_player(league_id: int):
    player_id = request.form.get("player_id")
    if not player_id:
        flash("Please select a player from suggestions", "warning")
        return redirect(url_for("roster.view", league_id=league_id))
    player = Player.query.get(player_id)
    if not player:
        flash("Selected player was not found in the database", "danger")
        return redirect(url_for("roster.view", league_id=league_id))
    exists = RosterEntry.query.filter_by(user_id=current_user.id, league_id=league_id, player_id=player.id).first()
    if exists:
        flash("Player already in roster", "info")
        return redirect(url_for("roster.view", league_id=league_id))
    db.session.add(RosterEntry(user_id=current_user.id, league_id=league_id, player_id=player.id))
    db.session.commit()
    flash("Player added", "success")
    return redirect(url_for("roster.view", league_id=league_id))


@roster_bp.route("/<int:league_id>/toggle/<int:entry_id>", methods=["POST"]) 
@login_required
def toggle_starter(league_id: int, entry_id: int):
    entry = RosterEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id or entry.league_id != league_id:
        flash("Not allowed", "danger")
        return redirect(url_for("roster.view", league_id=league_id))
    entry.is_starter = not entry.is_starter
    db.session.commit()
    return redirect(url_for("roster.view", league_id=league_id))


@roster_bp.route("/<int:league_id>/remove/<int:entry_id>", methods=["POST"]) 
@login_required
def remove_player(league_id: int, entry_id: int):
    entry = RosterEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id or entry.league_id != league_id:
        flash("Not allowed", "danger")
        return redirect(url_for("roster.view", league_id=league_id))
    db.session.delete(entry)
    db.session.commit()
    flash("Player removed", "success")
    return redirect(url_for("roster.view", league_id=league_id))


@roster_bp.route("/<int:league_id>/sitstart/<int:player_id>")
@login_required
def sit_start(league_id: int, player_id: int):
    player = Player.query.get_or_404(player_id)
    analysis = analyze_sit_start({
        "id": player.id,
        "name": player.name,
        "position": player.position,
        "team": player.team,
    }, team_context={"need_level": 0.5})
    return render_template("roster/sit_start.html", league_id=league_id, player=player, analysis=analysis)


