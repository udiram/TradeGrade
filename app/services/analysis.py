from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple
import math

import requests
import pandas as pd


@dataclass
class PlayerMetrics:
    player_id: int
    name: str
    position: str | None
    team: str | None
    projected_points: float
    injury_risk: float  # 0 to 1
    opponent_difficulty: float  # 0 (easy) to 1 (hard)
    recent_form: float  # -1 to +1


def _mock_projection(name: str, position: str | None) -> float:
    base = {
        "QB": 18.0,
        "RB": 14.0,
        "WR": 13.0,
        "TE": 9.0,
        "K": 8.0,
        "DEF": 7.0,
    }.get(position or "WR", 12.0)
    # Simple deterministic hash for stability
    salt = sum(ord(c) for c in name) % 7
    return base + salt * 0.8


def _mock_injury_risk(name: str) -> float:
    return (sum(ord(c) for c in name) % 10) / 20.0  # 0..0.45


def _mock_opponent_difficulty(team: str | None) -> float:
    if not team:
        return 0.5
    return (sum(ord(c) for c in team) % 10) / 10.0  # 0..0.9


def _mock_recent_form(name: str) -> float:
    return ((sum(ord(c) for c in name) % 10) - 5) / 5.0  # -1..+1


def compute_player_metrics(players: List[Dict]) -> List[PlayerMetrics]:
    metrics: List[PlayerMetrics] = []
    for p in players:
        name = p.get("name", "Unknown")
        position = p.get("position")
        team = p.get("team")
        metrics.append(
            PlayerMetrics(
                player_id=p["id"],
                name=name,
                position=position,
                team=team,
                projected_points=_mock_projection(name, position),
                injury_risk=_mock_injury_risk(name),
                opponent_difficulty=_mock_opponent_difficulty(team),
                recent_form=_mock_recent_form(name),
            )
        )
    return metrics


def _value_from_metrics(m: PlayerMetrics) -> float:
    # Simple valuation combining projections and adjustments
    adj = (
        - 4.0 * m.injury_risk
        - 2.5 * m.opponent_difficulty
        + 2.0 * m.recent_form
    )
    return m.projected_points + adj


def value_players(players: List[Dict]) -> Tuple[pd.DataFrame, float]:
    metrics = compute_player_metrics(players)
    rows = []
    for m in metrics:
        value = _value_from_metrics(m)
        rows.append({
            "id": m.player_id,
            "name": m.name,
            "position": m.position,
            "team": m.team,
            "proj": round(m.projected_points, 2),
            "injury": round(m.injury_risk, 3),
            "opp_diff": round(m.opponent_difficulty, 3),
            "form": round(m.recent_form, 3),
            "value": round(value, 2),
        })
    df = pd.DataFrame(rows)
    total = float(df["value"].sum()) if not df.empty else 0.0
    return df, total


def analyze_trade(offered: List[Dict], requested: List[Dict]) -> Dict:
    df_off, total_off = value_players(offered)
    df_req, total_req = value_players(requested)
    delta = total_req - total_off
    recommendation = "accept" if delta > 0.5 else ("decline" if delta < -0.5 else "neutral")
    return {
        "offered_table": df_off.to_dict(orient="records"),
        "requested_table": df_req.to_dict(orient="records"),
        "offered_total": round(total_off, 2),
        "requested_total": round(total_req, 2),
        "delta": round(delta, 2),
        "recommendation": recommendation,
    }


def analyze_sit_start(player: Dict, team_context: Dict | None = None) -> Dict:
    df, total = value_players([player])
    value = total
    # very simple team context adjustment placeholder
    synergy = float(team_context.get("need_level", 0.0)) if team_context else 0.0
    final = value + synergy
    decision = "start" if final >= (12.0 if (player.get("position") in {"RB", "WR"}) else 10.0) else "sit"
    return {
        "player": df.to_dict(orient="records")[0] if not df.empty else None,
        "team_need": synergy,
        "score": round(final, 2),
        "decision": decision,
    }


