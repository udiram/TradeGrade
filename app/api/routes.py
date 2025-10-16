from flask import Blueprint, request, jsonify

from ..models import Player
from ..services.players import search_players_cache, NFL_TEAMS, VALID_POSITIONS, TEAM_NICKNAMES


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/players")
def search_players():
    q = (request.args.get("q") or "").strip()
    query = Player.query
    
    if q:
        q_lower = q.lower()
        # Enhanced search for defenses with team nicknames
        from sqlalchemy import or_
        
        conditions = [Player.name.ilike(f"%{q}%")]
        
        # For defenses, also search by team nicknames
        for team_abbr, nicknames in TEAM_NICKNAMES.items():
            if any(q_lower in nickname.lower() for nickname in nicknames):
                conditions.append(
                    (Player.team == team_abbr) & (Player.position == 'DEF')
                )
        
        # Also search by team abbreviation
        if q_lower in [team.lower() for team in NFL_TEAMS]:
            conditions.append(Player.team == q_lower.upper())
            
        query = query.filter(or_(*conditions))
    
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


