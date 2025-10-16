from .extensions import db
from .models import Player


def seed_players_if_empty():
    try:
        if Player.query.count() > 0:
            return
    except Exception:
        # Tables don't exist yet, skip seeding
        return
    
    samples = [
        ("Patrick Mahomes", "QB", "KC"),
        ("Josh Allen", "QB", "BUF"),
        ("Jalen Hurts", "QB", "PHI"),
        ("Christian McCaffrey", "RB", "SF"),
        ("Bijan Robinson", "RB", "ATL"),
        ("CeeDee Lamb", "WR", "DAL"),
        ("Justin Jefferson", "WR", "MIN"),
        ("Ja'Marr Chase", "WR", "CIN"),
        ("Travis Kelce", "TE", "KC"),
        ("Amon-Ra St. Brown", "WR", "DET"),
    ]
    for name, pos, team in samples:
        db.session.add(Player(name=name, position=pos, team=team))
    db.session.commit()


