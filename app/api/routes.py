from flask import Blueprint, request, jsonify

from ..models import Player, RosterEntry, Membership
from ..services.players import search_players_cache, NFL_TEAMS, VALID_POSITIONS, TEAM_NICKNAMES


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/players")
def search_players():
    q = (request.args.get("q") or "").strip()
    query = Player.query
    
    # Easter egg: Rue Arlotta
    if q and ("rue arlotta" in q.lower() or (q.lower().startswith("rue") and len(q.strip()) <= 10)):
        return jsonify([{
            "id": "easter_egg_rue_arlotta",
            "name": "Rue Arlotta",
            "position": "RB",
            "team": "NE",
            "external_id": "easter_egg_rue_arlotta",
            "easter_egg": True,
            "stats": {
                "points_per_game": 100.0,
                "rushing_yards": 2000,
                "rushing_tds": 25,
                "receiving_yards": 800,
                "receiving_tds": 8,
                "fantasy_points": 1600
            }
        }])
    
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


@api_bp.get("/league/<int:user_id>/roster/<int:league_id>")
def get_user_roster(user_id: int, league_id: int):
    """Get a user's roster for trade proposals"""
    # Check if the user is a member of the league
    membership = Membership.query.filter_by(user_id=user_id, league_id=league_id).first()
    if not membership:
        return jsonify({"success": False, "error": "User not found in league"}), 404
    
    # Get the user's roster entries
    roster_entries = RosterEntry.query.filter_by(
        user_id=user_id, 
        league_id=league_id
    ).join(Player).order_by(Player.position, Player.name).all()
    
    # Format the response
    players = []
    for entry in roster_entries:
        players.append({
            "id": entry.id,  # RosterEntry ID for trade proposals
            "player_id": entry.player.id,
            "name": entry.player.name,
            "position": entry.player.position,
            "team": entry.player.team,
            "external_id": entry.player.external_id
        })
    
    return jsonify({"success": True, "players": players})


