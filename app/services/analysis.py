from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple
import math
import random

import os
import requests
import pandas as pd

try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except Exception:
    _GROQ_AVAILABLE = False


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
    # Easter egg: Special handling for Rue Arlotta
    rue_arlotta_in_offered = any(player.get('name') == 'Rue Arlotta' for player in offered)
    rue_arlotta_in_requested = any(player.get('name') == 'Rue Arlotta' for player in requested)
    
    if rue_arlotta_in_requested and not rue_arlotta_in_offered:
        # If you're getting Rue Arlotta, this is an amazing trade!
        return {
            "numeric_score": 100.0,
            "recommendation": "accept",
            "summary": "🎃 LEGENDARY TRADE ALERT! 🎃 You're getting Rue Arlotta, the most dominant running back in fantasy history! With 100 points per game, 2000+ rushing yards, and 25+ touchdowns, this is the trade of the century! Accept immediately before they realize their mistake! This fluffy Patriots RB will carry your team to victory! 🏆"
        }
    elif rue_arlotta_in_offered and not rue_arlotta_in_requested:
        # If you're giving away Rue Arlotta, this is a terrible trade!
        return {
            "numeric_score": -100.0,
            "recommendation": "decline",
            "summary": "🚨 TRADE DISASTER WARNING! 🚨 You're about to give away Rue Arlotta, the greatest fantasy player of all time! This fluffy Patriots RB puts up 100 points per game! Don't do it! Keep your legendary running back and dominate your league! 🎃"
        }
    
    df_off, total_off = value_players(offered)
    df_req, total_req = value_players(requested)
    delta = total_req - total_off
    recommendation = "accept" if delta > 0.5 else ("decline" if delta < -0.5 else "neutral")
    
    # Enhanced analysis with position breakdowns and risk assessment
    off_metrics = compute_player_metrics(offered)
    req_metrics = compute_player_metrics(requested)
    
    # Position analysis
    off_positions = {}
    req_positions = {}
    for m in off_metrics:
        pos = m.position or "UNKNOWN"
        if pos not in off_positions:
            off_positions[pos] = {"count": 0, "total_value": 0.0, "avg_value": 0.0}
        off_positions[pos]["count"] += 1
        off_positions[pos]["total_value"] += _value_from_metrics(m)
    
    for m in req_metrics:
        pos = m.position or "UNKNOWN"
        if pos not in req_positions:
            req_positions[pos] = {"count": 0, "total_value": 0.0, "avg_value": 0.0}
        req_positions[pos]["count"] += 1
        req_positions[pos]["total_value"] += _value_from_metrics(m)
    
    # Calculate averages
    for pos_data in off_positions.values():
        pos_data["avg_value"] = pos_data["total_value"] / pos_data["count"]
    for pos_data in req_positions.values():
        pos_data["avg_value"] = pos_data["total_value"] / pos_data["count"]
    
    # Risk analysis
    off_risk = sum(m.injury_risk for m in off_metrics) / len(off_metrics) if off_metrics else 0
    req_risk = sum(m.injury_risk for m in req_metrics) / len(req_metrics) if req_metrics else 0
    risk_delta = req_risk - off_risk
    
    # Upside analysis (projected points)
    off_upside = sum(m.projected_points for m in off_metrics) / len(off_metrics) if off_metrics else 0
    req_upside = sum(m.projected_points for m in req_metrics) / len(req_metrics) if req_metrics else 0
    upside_delta = req_upside - off_upside
    
    # Generate AI summary
    try:
        ai_summary = generate_trade_summary(offered, requested, {
            "delta": delta,
            "recommendation": recommendation,
            "off_positions": off_positions,
            "req_positions": req_positions,
            "risk_delta": risk_delta,
            "upside_delta": upside_delta,
        })
    except Exception as e:
        print(f"AI summary generation failed: {e}")
        ai_summary = {
            "summary": f"Trade analysis completed. Score: {delta:+.1f}. Recommendation: {recommendation.title()}.",
            "recommendation": recommendation,
            "bullets": [],
            "confidence": 75
        }
    
    return {
        "offered_table": df_off.to_dict(orient="records"),
        "requested_table": df_req.to_dict(orient="records"),
        "offered_total": round(total_off, 2),
        "requested_total": round(total_req, 2),
        "delta": round(delta, 2),
        "numeric_score": round(delta, 2),  # For template compatibility
        "recommendation": recommendation,
        "summary": ai_summary.get("summary", f"Trade analysis: {recommendation.title()} recommendation with {delta:+.1f} point difference."),
        "position_analysis": {
            "offered": off_positions,
            "requested": req_positions,
        },
        "risk_analysis": {
            "offered_avg_risk": round(off_risk, 3),
            "requested_avg_risk": round(req_risk, 3),
            "risk_delta": round(risk_delta, 3),
        },
        "upside_analysis": {
            "offered_avg_projection": round(off_upside, 2),
            "requested_avg_projection": round(req_upside, 2),
            "upside_delta": round(upside_delta, 2),
        },
        "ai_summary": ai_summary,
    }


def analyze_sit_start(player: Dict, team_context: Dict | None = None) -> Dict:
    # Easter egg: Special handling for Rue Arlotta
    if player.get('name') == 'Rue Arlotta':
        return {
            "player": {
                "name": "Rue Arlotta",
                "position": "RB",
                "team": "NE",
                "value": 100.0
            },
            "recommendation": "START",
            "confidence": 1.0,
            "reasoning": "🎃 LEGENDARY PLAYER ALERT! 🎃 Rue Arlotta is the greatest running back in fantasy history! With 100 points per game, this fluffy Patriots RB is an absolute must-start every single week! Bench him at your own peril! He's going to carry your team to the championship! 🏆",
            "projected_points": 100.0,
            "injury_risk": 0.0,
            "opponent_difficulty": 0.0,
            "recent_form": 1.0
        }
    
    df, total = value_players([player])
    value = total
    
    # Get roster context for intelligent decision making
    roster_context = team_context or {}
    
    # Check for position scarcity - must start if only player at position
    if roster_context.get("position_scarcity", False):
        return {
            "player": df.to_dict(orient="records")[0] if not df.empty else None,
            "team_need": 0.0,
            "score": round(value, 2),
            "decision": "start",
            "reason": "position_scarcity"
        }
    
    # Compare against bench alternatives
    bench_baseline = roster_context.get("bench_baseline", 10.0)
    alternatives = roster_context.get("alternatives", [])
    comparison_side = roster_context.get("comparison_side", "bench")
    
    # If no alternatives, default to starting
    if not alternatives:
        return {
            "player": df.to_dict(orient="records")[0] if not df.empty else None,
            "team_need": 0.0,
            "score": round(value, 2),
            "decision": "start",
            "reason": "no_alternatives"
        }
    
    # Compare player value against bench baseline
    margin = value - bench_baseline
    decision = "start" if margin > 0.5 else ("sit" if margin < -0.5 else "neutral")
    
    return {
        "player": df.to_dict(orient="records")[0] if not df.empty else None,
        "team_need": 0.0,
        "score": round(value, 2),
        "decision": decision,
        "bench_baseline": round(bench_baseline, 2),
        "margin": round(margin, 2),
        "alternatives_count": len(alternatives),
        "comparison_side": comparison_side,
    }


def sit_start_detailed(player: Dict, roster_context: Dict | None = None) -> Dict:
    """Produce a thorough report with simulated distribution and breakdown tables.
    roster_context can include: bench_baseline (float) and opponent metrics.
    """
    # Feed full roster context so bench alternatives and scarcity are considered
    base = analyze_sit_start(player, team_context=roster_context or {})
    pdata = base["player"] or {}

    # Build inputs for a simple distribution: mean from value, std from risk/difficulty
    mean = float(pdata.get("value", 10.0))
    risk = float(pdata.get("injury", 0.2))
    opp = float(pdata.get("opp_diff", 0.5))
    std = max(2.0, 4.0 + 3.0 * (risk + opp - 0.5))

    # Monte Carlo simulation
    samples = [random.gauss(mu=mean, sigma=std) for _ in range(5000)]
    samples = [max(0.0, round(x, 2)) for x in samples]
    samples.sort()
    percentiles = {
        "p10": round(samples[int(0.10 * len(samples))], 2),
        "p25": round(samples[int(0.25 * len(samples))], 2),
        "p50": round(samples[int(0.50 * len(samples))], 2),
        "p75": round(samples[int(0.75 * len(samples))], 2),
        "p90": round(samples[int(0.90 * len(samples))], 2),
    }

    bench = float((roster_context or {}).get("bench_baseline", 10.0))
    win_prob = round(sum(1 for s in samples if s >= bench) / len(samples), 3)

    # tiny table for visualization
    hist_bins = 20
    bin_edges = [min(samples) + i * (max(samples) - min(samples)) / hist_bins for i in range(hist_bins + 1)]
    counts = [0] * hist_bins
    for s in samples:
        # find bin
        idx = min(hist_bins - 1, int((s - bin_edges[0]) / (bin_edges[-1] - bin_edges[0]) * hist_bins))
        counts[idx] += 1

    return {
        **base,
        "distribution": {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "percentiles": percentiles,
            "hist": {"edges": [round(x, 2) for x in bin_edges], "counts": counts},
            "win_prob_vs_bench": win_prob,
            "bench_baseline": bench,
        },
        "breakdown": {
            "projection": pdata.get("proj"),
            "injury_risk": pdata.get("injury"),
            "opponent_difficulty": pdata.get("opp_diff"),
            "recent_form": pdata.get("form"),
        },
        "context": build_player_context(player),
        "alternatives": (roster_context or {}).get("alternatives_detailed", []),
        "llm": llm_summarize(player, base, {
            "mean": mean,
            "std": std,
            "percentiles": percentiles,
            "win_prob": win_prob,
            "bench": bench,
        })
    }


def build_player_context(player: Dict) -> Dict:
    name = player.get("name") or ""
    team = player.get("team") or ""
    position = player.get("position") or ""
    headlines = fetch_news(name, team)
    opponent = estimate_next_opponent(team)
    opp_metrics = fetch_opponent_metrics(opponent) if opponent else {}
    recent_stats = fetch_recent_stats(name, team)
    return {
        "headlines": headlines[:8],
        "opponent": opponent,
        "opponent_metrics": opp_metrics,
        "recent_stats": recent_stats,
    }


def fetch_news(name: str, team: str) -> List[str]:
    q = f"{name} {team} fantasy football OR injury OR status"
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=en-US&gl=US&ceid=US:en"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        titles: List[str] = []
        for item in root.findall('.//item'):
            title_el = item.find('title')
            if title_el is not None and title_el.text:
                titles.append(title_el.text)
        return titles
    except Exception:
        return []


def estimate_next_opponent(team: str | None) -> str | None:
    if not team:
        return None
    # Placeholder rotation based on hash; in a production app, wire official schedule
    teams = [
        "ARI","ATL","BAL","BUF","CAR","CHI","CIN","CLE","DAL","DEN","DET","GB","HOU","IND","JAX","KC","LV","LAC","LAR","MIA","MIN","NE","NO","NYG","NYJ","PHI","PIT","SEA","SF","TB","TEN","WAS"
    ]
    idx = (sum(ord(c) for c in team) % len(teams))
    return teams[(idx + 5) % len(teams)]


def fetch_opponent_metrics(team: str) -> Dict:
    # Try a lightweight public dataset: if unavailable, synthesize a stable value
    try:
        # Dummy endpoint placeholder; replace with real defensive rankings source
        # resp = requests.get('https://api.example.com/nfl/defense_rankings', timeout=5)
        # data = resp.json()
        pass
    except Exception:
        pass
    difficulty = (sum(ord(c) for c in team) % 10) / 10.0
    epa_rank = 32 - (sum(ord(c) for c in team) % 32)
    pace_rank = (sum(ord(c) for c in team[::-1]) % 32) + 1
    return {"difficulty_index": difficulty, "epa_pass_rank": epa_rank, "pace_rank": pace_rank}


def fetch_recent_stats(name: str, team: str) -> List[Dict]:
    # In a real app, pull last 4 games from a provider; here we synthesize but stable
    base = (sum(ord(c) for c in name + team) % 8) + 10
    return [{"week": i, "points": round(base + random.uniform(-3, 3), 1)} for i in range(1, 5)]


def llm_summarize(player: Dict, base: Dict, dist: Dict) -> Dict:
    if not _GROQ_AVAILABLE:
        return {"summary": "LLM unavailable.", "bullets": [], "final": base.get("decision","start")}
    
    from flask import current_app
    groq_key = current_app.config.get("GROQ_API_KEY")
    if not groq_key:
        return {"summary": "GROQ_API_KEY not set.", "bullets": [], "final": base.get("decision","start")}
    client = Groq(api_key=groq_key)
    name = player.get("name"); pos = player.get("position"); team = player.get("team")
    ctx = build_player_context(player)
    
    # Build bench comparison context
    bench_info = ""
    if base.get("reason") == "position_scarcity":
        bench_info = f"CRITICAL: {name} is the ONLY {pos} on the roster - MUST START."
    elif base.get("reason") == "no_alternatives":
        bench_info = f"No bench alternatives at {pos} position - default to START."
    else:
        bench_baseline = base.get("bench_baseline", 0)
        margin = base.get("margin", 0)
        alt_count = base.get("alternatives_count", 0)
        bench_info = f"Bench comparison: {alt_count} alternatives averaging {bench_baseline} points. Margin: {margin:+0.1f} points vs bench."
    
    prompt = (
        f"You are a fantasy football assistant. Recommend SIT or START for {name} ({pos}, {team}).\n"
        f"Key numbers: score={base.get('score')}, proj={base.get('player',{}).get('proj')}, injury={base.get('player',{}).get('injury')},"
        f" opp_diff={base.get('player',{}).get('opp_diff')}, form={base.get('player',{}).get('form')}.\n"
        f"{bench_info}\n"
        f"Distribution analysis: mean={dist['mean']}, p50={dist['percentiles']['p50']}, win_prob={dist['win_prob']}.\n"
        f"Opponent metrics: {ctx.get('opponent')} -> {ctx.get('opponent_metrics')}. Recent stats: {ctx.get('recent_stats')}.\n"
        f"Headlines: {ctx.get('headlines')}.\n"
        "Return concise JSON with fields: final ('start'|'sit'), summary (2-3 sentences), bullets (3-5 short bullets). Focus on bench comparison and practical decision."
    )
    models = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ]
    last_err = None
    import json, re
    for m in models:
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=[{"role":"user","content":prompt}],
                response_format={"type":"json_object"}
            )
            content = resp.choices[0].message.content
            try:
                data = json.loads(content)
            except Exception:
                # Try to extract json substring
                match = re.search(r"\{[\s\S]*\}", content)
                data = json.loads(match.group(0)) if match else {}
            return {
                "final": data.get("final", base.get("decision")),
                "summary": data.get("summary", ""),
                "bullets": data.get("bullets", []),
            }
        except Exception as e:
            last_err = str(e)
            continue
    return {"summary": "LLM summarization failed.", "bullets": [], "final": base.get("decision","start"), "error": last_err}


def generate_trade_summary(offered: List[Dict], requested: List[Dict], analysis: Dict) -> Dict:
    """Generate AI-powered trade analysis summary."""
    if not _GROQ_AVAILABLE:
        return {"summary": "AI analysis unavailable.", "recommendation": analysis["recommendation"], "bullets": []}
    
    from flask import current_app
    groq_key = current_app.config.get("GROQ_API_KEY")
    if not groq_key:
        return {"summary": "GROQ_API_KEY not set.", "recommendation": analysis["recommendation"], "bullets": [], "confidence": 50}
    client = Groq(api_key=groq_key)
    
    # Build context for AI
    offered_names = [p["name"] for p in offered]
    requested_names = [p["name"] for p in requested]
    
    prompt = f"""You are a fantasy football trade analyst. Analyze this trade proposal:

TRADING AWAY: {', '.join(offered_names)}
RECEIVING: {', '.join(requested_names)}

KEY METRICS:
- Value Delta: {analysis['delta']:+0.1f} points ({analysis['recommendation']})
- Risk Change: {analysis['risk_delta']:+0.3f} (negative = less risky)
- Upside Change: {analysis['upside_delta']:+0.1f} projected points

POSITION BREAKDOWN:
Offered: {analysis['off_positions']}
Requested: {analysis['req_positions']}

Provide a comprehensive trade analysis in JSON format with:
- "recommendation": "accept", "decline", or "neutral"
- "summary": 2-3 sentence executive summary
- "bullets": 4-6 key points covering value, risk, position needs, and strategic considerations
- "confidence": 0-100 confidence in recommendation

Focus on practical fantasy football implications, roster construction, and long-term value."""
    
    models = ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    last_err = None
    import json, re
    
    for m in models:
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=[{"role":"user","content":prompt}],
                response_format={"type":"json_object"}
            )
            content = resp.choices[0].message.content
            try:
                data = json.loads(content)
            except Exception:
                # Try to extract json substring
                match = re.search(r"\{[\s\S]*\}", content)
                data = json.loads(match.group(0)) if match else {}
            
            return {
                "recommendation": data.get("recommendation", analysis["recommendation"]),
                "summary": data.get("summary", ""),
                "bullets": data.get("bullets", []),
                "confidence": data.get("confidence", 75),
            }
        except Exception as e:
            last_err = str(e)
            continue
    
    return {
        "recommendation": analysis["recommendation"],
        "summary": "AI analysis failed.",
        "bullets": [],
        "confidence": 50,
        "error": last_err
    }


