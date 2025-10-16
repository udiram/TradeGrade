from flask import Blueprint, request, jsonify

from ..models import Player
from ..services.players import search_players_cache, NFL_TEAMS, VALID_POSITIONS


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/players")
def search_players():
    q = (request.args.get("q") or "").strip()
    query = Player.query
    if q:
        like = f"%{q}%"
        query = query.filter(Player.name.ilike(like))
    # Restrict to active NFL-shaped entries in DB
    db_players = (
        query.filter(
            (Player.position.in_(list(VALID_POSITIONS))) &
            ((Player.team.in_(list(NFL_TEAMS))) | (Player.position == 'DEF'))
        )
        .order_by(Player.name)
        .limit(15)
        .all()
    )
    cached = search_players_cache(q, limit=20)
    # Merge results, preferring DB when names match
    merged = []
    seen = set()
    for p in db_players:
        merged.append({"id": p.id, "name": p.name, "position": p.position, "team": p.team})
        seen.add((p.name or "").lower())
    for p in cached:
        key = (p.get("name") or "").lower()
        if key in seen:
            continue
        merged.append({"id": None, "name": p.get("name"), "position": p.get("position"), "team": p.get("team")})
    return jsonify(merged[:20])


