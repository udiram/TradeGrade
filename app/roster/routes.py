from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..extensions import db
from ..models import League, Membership, Player, RosterEntry
from ..services.analysis import analyze_sit_start, sit_start_detailed


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
    # Get the player
    player = Player.query.get_or_404(player_id)
    
    # Get all roster entries for this user in this league
    all_entries = (
        RosterEntry.query.filter_by(user_id=current_user.id, league_id=league_id)
        .join(Player)
        .order_by(Player.position, Player.name)
        .all()
    )
    
    # Build roster context with bench alternatives
    roster_context = build_roster_context(player, all_entries)
    
    analysis = sit_start_detailed({
        "id": player.id,
        "name": player.name,
        "position": player.position,
        "team": player.team,
    }, roster_context=roster_context)
    
    return render_template("roster/sit_start.html", league_id=league_id, player=player, analysis=analysis)


def build_roster_context(target_player: Player, all_entries: list) -> dict:
    """Build context about bench alternatives for sit/start analysis."""
    def normalize_position(pos: str | None) -> str:
        if not pos:
            return ""
        p = pos.strip().upper()
        # Common aliases
        if p in {"PK", "K"}:
            return "K"
        if p in {"D/ST", "DST", "DEF"}:
            return "DEF"
        if p in {"QB", "RB", "WR", "TE", "FLEX"}:
            return p
        # Default: return uppercase trimmed
        return p

    target_position = normalize_position(target_player.position)
    
    # Separate starters and bench players by position
    starters_by_pos = {}
    bench_by_pos = {}
    
    for entry in all_entries:
        pos = normalize_position(entry.player.position)
        if pos not in starters_by_pos:
            starters_by_pos[pos] = []
            bench_by_pos[pos] = []
        
        if entry.is_starter:
            starters_by_pos[pos].append(entry.player)
        else:
            bench_by_pos[pos].append(entry.player)
    
    # Find the target player's current status
    target_is_starter = any(
        entry.player_id == target_player.id and entry.is_starter 
        for entry in all_entries
    )
    
    # Get alternatives based on which side the target is currently on
    # If target is a starter, compare to BENCH at the same position (and flex if needed)
    # If target is on bench, compare to STARTERS at the same position
    comparison_side = "bench" if target_is_starter else "starters"
    if target_is_starter:
        pool = bench_by_pos
    else:
        pool = starters_by_pos

    if target_position in pool:
        alternatives = pool[target_position]
    else:
        # If no players at this position on the comparison side, allow flex search only when
        # the position is eligible for common flex spots (RB/WR/TE)
        alternatives = []
        if target_position in {"RB", "WR", "TE"}:
            for pos in ["RB", "WR", "TE"]:
                if pos in pool:
                    alternatives.extend(pool[pos])

    # Exclude the target player from the alternatives pool, if present
    alternatives = [p for p in alternatives if p.id != target_player.id]
    
    # Calculate position scarcity
    total_at_position = len(starters_by_pos.get(target_position, [])) + len(bench_by_pos.get(target_position, []))
    position_scarcity = total_at_position <= 1  # Must start if only player at position
    
    # Calculate bench baseline (average projection of alternatives) and per-alt details
    alt_details = []
    if alternatives:
        from ..services.analysis import compute_player_metrics
        alt_input = [{
            "id": p.id, "name": p.name, "position": p.position, "team": p.team
        } for p in alternatives]
        alt_metrics = compute_player_metrics(alt_input)
        bench_baseline = sum(m.projected_points for m in alt_metrics) / len(alt_metrics)
        # attach projections to alternatives in same order
        for p, m in zip(alternatives, alt_metrics):
            alt_details.append({
                "id": p.id,
                "name": p.name,
                "position": normalize_position(p.position),
                "team": p.team,
                "proj": round(m.projected_points, 2)
            })
    else:
        bench_baseline = 8.0  # Default fallback
    
    return {
        "target_is_starter": target_is_starter,
        "position_scarcity": position_scarcity,
        "alternatives": [{"id": p.id, "name": p.name, "position": normalize_position(p.position), "team": p.team} for p in alternatives],
        "alternatives_detailed": alt_details,
        "comparison_side": comparison_side,
        "bench_baseline": bench_baseline,
        "total_at_position": total_at_position,
        "starters_at_position": len(starters_by_pos.get(target_position, [])),
        "bench_at_position": len(bench_by_pos.get(target_position, [])),
    }


