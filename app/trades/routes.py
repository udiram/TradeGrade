from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..extensions import db, socketio
from ..models import League, Membership, Player, Trade
from ..services.analysis import analyze_trade
from ..services.sentiment import stream_sentiment_events


trades_bp = Blueprint("trades", __name__, url_prefix="/trades")


@trades_bp.route("/<int:league_id>", methods=["GET", "POST"]) 
@login_required
def analyze(league_id: int):
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))

    if request.method == "POST":
        offered_names = [n.strip() for n in request.form.get("offered", "").split(",") if n.strip()]
        requested_names = [n.strip() for n in request.form.get("requested", "").split(",") if n.strip()]
        offered_players = Player.query.filter(Player.name.in_(offered_names)).all()
        requested_players = Player.query.filter(Player.name.in_(requested_names)).all()

        trade = Trade(
            league_id=league_id,
            proposer_id=current_user.id,
            offered_player_ids=",".join(str(p.id) for p in offered_players),
            requested_player_ids=",".join(str(p.id) for p in requested_players),
        )
        db.session.add(trade)
        db.session.commit()
        # Perform quick numeric analysis synchronously for MVP
        offered_dicts = [{"id": p.id, "name": p.name, "position": p.position, "team": p.team} for p in offered_players]
        requested_dicts = [{"id": p.id, "name": p.name, "position": p.position, "team": p.team} for p in requested_players]
        result = analyze_trade(offered_dicts, requested_dicts)
        trade.numeric_score = result["delta"]
        trade.recommendation = result["recommendation"]
        trade.summary = (
            f"Offered total: {result['offered_total']} vs Requested total: {result['requested_total']} | "
            f"Delta: {result['delta']} => {result['recommendation']}"
        )
        db.session.commit()
        # Kick off brief sentiment stream to the trade room
        room = f"trade-{trade.id}"
        player_names = [p.name for p in offered_players + requested_players]
        socketio.start_background_task(stream_sentiment_events, socketio, room, player_names)
        flash("Trade analyzed.", "info")
        return redirect(url_for("trades.result", league_id=league_id, trade_id=trade.id))

    return render_template("trades/analyze.html", league_id=league_id)


@trades_bp.route("/<int:league_id>/result/<int:trade_id>")
@login_required
def result(league_id: int, trade_id: int):
    trade = Trade.query.get_or_404(trade_id)
    if trade.league_id != league_id:
        flash("Not allowed", "danger")
        return redirect(url_for("league.dashboard"))
    offered_ids = [int(x) for x in trade.offered_player_ids.split(",") if x]
    requested_ids = [int(x) for x in trade.requested_player_ids.split(",") if x]
    offered = Player.query.filter(Player.id.in_(offered_ids)).all() if offered_ids else []
    requested = Player.query.filter(Player.id.in_(requested_ids)).all() if requested_ids else []
    return render_template("trades/result.html", league_id=league_id, trade=trade, offered=offered, requested=requested)


