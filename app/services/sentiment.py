from __future__ import annotations

from typing import Dict, List
import time
import random

import httpx


def fetch_headlines_for_player(name: str) -> List[str]:
    # Placeholder fetch; integrate NewsAPI/Twitter in production
    return [
        f"{name} shows promising form in practice",
        f"Coach comments on {name}'s role this week",
        f"Beat reporter: matchup outlook for {name}",
    ]


def analyze_sentiment(texts: List[str]) -> Dict:
    # Simple random mock sentiment; replace with OpenAI or fine-tuned model
    if not texts:
        return {"score": 0.0, "label": "neutral"}
    score = sum(random.uniform(-0.2, 0.2) for _ in texts)
    label = "positive" if score > 0.2 else ("negative" if score < -0.2 else "neutral")
    return {"score": round(score, 3), "label": label}


def stream_sentiment_events(socketio, room: str, players: List[str]) -> None:
    # Emits periodic updates with random fluctuations
    for _ in range(5):
        updates = []
        for name in players:
            headlines = fetch_headlines_for_player(name)
            sent = analyze_sentiment(headlines)
            updates.append({"player": name, "sentiment": sent, "headlines": headlines[:2]})
        socketio.emit("sentiment_update", {"updates": updates}, room=room)
        time.sleep(2)


