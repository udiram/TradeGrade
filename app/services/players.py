from __future__ import annotations

import threading
from typing import Dict, List
import requests
from datetime import datetime

NFL_TEAMS = {
    "ARI","ATL","BAL","BUF","CAR","CHI","CIN","CLE","DAL","DEN",
    "DET","GB","HOU","IND","JAX","KC","LV","LAC","LAR","MIA",
    "MIN","NE","NO","NYG","NYJ","PHI","PIT","SEA","SF","TB","TEN","WAS"
}
VALID_POSITIONS = {"QB", "RB", "WR", "TE", "K", "DEF"}

# Team nickname mappings for better search
TEAM_NICKNAMES = {
    "ARI": ["cardinals", "arizona"],
    "ATL": ["falcons", "atlanta"],
    "BAL": ["ravens", "baltimore"],
    "BUF": ["bills", "buffalo"],
    "CAR": ["panthers", "carolina"],
    "CHI": ["bears", "chicago"],
    "CIN": ["bengals", "cincinnati"],
    "CLE": ["browns", "cleveland"],
    "DAL": ["cowboys", "dallas"],
    "DEN": ["broncos", "denver"],
    "DET": ["lions", "detroit"],
    "GB": ["packers", "green bay"],
    "HOU": ["texans", "houston"],
    "IND": ["colts", "indianapolis"],
    "JAX": ["jaguars", "jacksonville"],
    "KC": ["chiefs", "kansas city"],
    "LV": ["raiders", "las vegas", "oakland"],
    "LAC": ["chargers", "los angeles"],
    "LAR": ["rams", "los angeles"],
    "MIA": ["dolphins", "miami"],
    "MIN": ["vikings", "minnesota"],
    "NE": ["patriots", "new england"],
    "NO": ["saints", "new orleans"],
    "NYG": ["giants", "new york"],
    "NYJ": ["jets", "new york"],
    "PHI": ["eagles", "philadelphia"],
    "PIT": ["steelers", "pittsburgh"],
    "SEA": ["seahawks", "seattle"],
    "SF": ["49ers", "niners", "san francisco"],
    "TB": ["buccaneers", "bucs", "tampa bay"],
    "TEN": ["titans", "tennessee"],
    "WAS": ["commanders", "washington", "redskins"]
}


def is_active_nfl_player(p: Dict) -> bool:
    # Sleeper fields: active(bool), team (abbr), position
    if not p:
        return False
    if not p.get("active", False):
        return False
    pos = p.get("position")
    team = p.get("team")
    if pos not in VALID_POSITIONS:
        return False
    if team not in NFL_TEAMS and pos != "DEF":
        return False
    name = p.get("full_name") or p.get("first_name")
    return bool(name)


_players_lock = threading.Lock()
_players_cache: List[Dict] | None = None


def _fetch_all_players_from_sleeper() -> List[Dict]:
    # Sleeper returns a large JSON of all nfl players
    url = "https://api.sleeper.app/v1/players/nfl"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()  # dict keyed by player_id
    players: List[Dict] = []
    for pid, p in data.items():
        if not is_active_nfl_player(p):
            continue
        name = p.get("full_name") or p.get("first_name") or ""
        position = p.get("position")
        team = p.get("team")
        # Capture injury status
        injury_status = p.get("injury_status") or None  # OUT, Doubtful, Questionable, etc.
        
        players.append({
            "external_id": str(pid),
            "name": name,
            "position": position,
            "team": team,
            "injury_status": injury_status,  # ADD THIS
        })
    return players


def warm_players_cache(force: bool = False) -> None:
    global _players_cache
    with _players_lock:
        if _players_cache is not None and not force:
            return
        try:
            _players_cache = _fetch_all_players_from_sleeper()
        except Exception:
            _players_cache = []


def search_players_cache(query: str, limit: int = 20) -> List[Dict]:
    global _players_cache
    if _players_cache is None:
        warm_players_cache()
    if not query:
        return []
    q = query.lower()
    results = []
    
    for p in (_players_cache or []):
        name = (p.get("name") or "").lower()
        team = p.get("team", "")
        position = p.get("position", "")
        
        # Check if query matches name
        if q in name:
            results.append(p)
            continue
            
        # For defenses, also check team nicknames
        if position == "DEF" and team in TEAM_NICKNAMES:
            nicknames = TEAM_NICKNAMES[team]
            if any(q in nickname.lower() for nickname in nicknames):
                results.append(p)
                continue
                
        # Check if query matches team abbreviation
        if q == team.lower():
            results.append(p)
    
    return results[:limit]


def sync_player_injury_status(player) -> None:
    """Fetch and update injury status for a specific player from Sleeper API."""
    if not player.external_id:
        return
    
    try:
        url = "https://api.sleeper.app/v1/players/nfl"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        player_data = data.get(player.external_id)
        if player_data:
            injury_status = player_data.get("injury_status")
            player.injury_status = injury_status
            player.injury_updated_at = datetime.utcnow()
            from app.extensions import db
            db.session.commit()
    except Exception as e:
        print(f"Failed to sync injury status for {player.name}: {e}")


def get_injury_severity_score(injury_status: str | None) -> float:
    """Convert injury status to a severity score (0.0 = healthy, 1.0 = out)."""
    if not injury_status:
        return 0.0
    
    status_map = {
        "Out": 1.0,
        "OUT": 1.0,
        "IR": 1.0,
        "PUP": 1.0,
        "Suspended": 1.0,
        "Doubtful": 0.85,
        "Questionable": 0.4,
        "Probable": 0.15,
    }
    
    return status_map.get(injury_status, 0.0)


# DB sync helpers
def sync_active_players_into_db(db, Player) -> int:
    """Ensure all cached active NFL players exist in DB (by name+team+position). Returns new count."""
    warm_players_cache()
    cache = _players_cache or []
    created = 0
    updated = 0
    for p in cache:
        existing = Player.query.filter_by(name=p["name"], team=p["team"], position=p["position"]).first()
        if existing:
            # Update injury status for existing players
            if existing.injury_status != p.get("injury_status"):
                existing.injury_status = p.get("injury_status")
                existing.injury_updated_at = datetime.utcnow()
                updated += 1
            continue
        db.session.add(Player(
            name=p["name"], 
            team=p["team"], 
            position=p["position"], 
            external_id=p.get("external_id"),
            injury_status=p.get("injury_status"),
            injury_updated_at=datetime.utcnow()
        ))
        created += 1
    if created or updated:
        db.session.commit()
    return created


def purge_non_nfl_players(db, Player) -> int:
    """Delete players not matching NFL team/position constraints."""
    to_delete = Player.query.filter(
        (Player.position.notin_(list(VALID_POSITIONS))) |
        ((Player.team.notin_(list(NFL_TEAMS))) & (Player.position != "DEF"))
    ).all()
    count = len(to_delete)
    for p in to_delete:
        db.session.delete(p)
    if count:
        db.session.commit()
    return count


