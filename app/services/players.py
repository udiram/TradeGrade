from __future__ import annotations

import threading
from typing import Dict, List
import requests

NFL_TEAMS = {
    "ARI","ATL","BAL","BUF","CAR","CHI","CIN","CLE","DAL","DEN",
    "DET","GB","HOU","IND","JAX","KC","LV","LAC","LAR","MIA",
    "MIN","NE","NO","NYG","NYJ","PHI","PIT","SEA","SF","TB","TEN","WAS"
}
VALID_POSITIONS = {"QB", "RB", "WR", "TE", "K", "DEF"}


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
        players.append({
            "external_id": str(pid),
            "name": name,
            "position": position,
            "team": team,
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
    results = [p for p in (_players_cache or []) if q in (p.get("name") or "").lower()]
    return results[:limit]


# DB sync helpers
def sync_active_players_into_db(db, Player) -> int:
    """Ensure all cached active NFL players exist in DB (by name+team+position). Returns new count."""
    warm_players_cache()
    cache = _players_cache or []
    created = 0
    for p in cache:
        existing = Player.query.filter_by(name=p["name"], team=p["team"], position=p["position"]).first()
        if existing:
            continue
        db.session.add(Player(name=p["name"], team=p["team"], position=p["position"], external_id=p.get("external_id")))
        created += 1
    if created:
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


