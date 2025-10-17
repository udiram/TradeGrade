"""
Activity logging service for tracking league events
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import current_app
from app import db
from app.models import LeagueActivity, User, League, RosterEntry, Player, TradeProposal, BoardPost


def log_activity(
    league_id: int,
    activity_type: str,
    title: str,
    description: str,
    user_id: Optional[int] = None,
    activity_metadata: Optional[Dict[str, Any]] = None
) -> LeagueActivity:
    """Log a new league activity"""
    activity = LeagueActivity(
        league_id=league_id,
        user_id=user_id,
        activity_type=activity_type,
        title=title,
        description=description,
        activity_data=json.dumps(activity_metadata) if activity_metadata else None
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return activity


def log_trade_proposal(proposal: TradeProposal) -> LeagueActivity:
    """Log a trade proposal activity"""
    # Get player names for the description
    offered_names = _get_player_names_from_ids(proposal.offered_player_ids.split(','))
    requested_names = _get_player_names_from_ids(proposal.requested_player_ids.split(','))
    
    title = f"Trade Proposal: {proposal.proposer.display_name or proposal.proposer.email} → {proposal.recipient.display_name or proposal.recipient.email}"
    description = f"<strong>{proposal.proposer.display_name or proposal.proposer.email}</strong> proposed trading <strong>{', '.join(offered_names)}</strong> for <strong>{', '.join(requested_names)}</strong>"
    
    if proposal.message:
        description += f"<br><em>\"{proposal.message}\"</em>"
    
    metadata = {
        "proposal_id": proposal.id,
        "proposer_id": proposal.proposer_id,
        "recipient_id": proposal.recipient_id,
        "offered_players": offered_names,
        "requested_players": requested_names,
        "has_message": bool(proposal.message)
    }
    
    return log_activity(
        league_id=proposal.league_id,
        activity_type="trade_proposal",
        title=title,
        description=description,
        user_id=proposal.proposer_id,
        activity_metadata=metadata
    )


def log_trade_response(proposal: TradeProposal, response: str) -> LeagueActivity:
    """Log a trade proposal response (accepted/rejected)"""
    offered_names = _get_player_names_from_ids(proposal.offered_player_ids.split(','))
    requested_names = _get_player_names_from_ids(proposal.requested_player_ids.split(','))
    
    if response == "accepted":
        title = f"Trade Accepted: {proposal.proposer.display_name or proposal.proposer.email} ↔ {proposal.recipient.display_name or proposal.recipient.email}"
        description = f"<strong>{proposal.recipient.display_name or proposal.recipient.email}</strong> accepted the trade: <strong>{', '.join(offered_names)}</strong> for <strong>{', '.join(requested_names)}</strong>"
        activity_type = "trade_accepted"
    else:
        title = f"Trade Declined: {proposal.proposer.display_name or proposal.proposer.email} → {proposal.recipient.display_name or proposal.recipient.email}"
        description = f"<strong>{proposal.recipient.display_name or proposal.recipient.email}</strong> declined the trade proposal"
        activity_type = "trade_rejected"
    
    metadata = {
        "proposal_id": proposal.id,
        "proposer_id": proposal.proposer_id,
        "recipient_id": proposal.recipient_id,
        "offered_players": offered_names,
        "requested_players": requested_names,
        "response": response
    }
    
    return log_activity(
        league_id=proposal.league_id,
        activity_type=activity_type,
        title=title,
        description=description,
        user_id=proposal.recipient_id,
        activity_metadata=metadata
    )


def log_roster_add(league_id: int, user_id: int, player: Player, roster_entry: RosterEntry) -> LeagueActivity:
    """Log a roster addition"""
    title = f"Roster Addition: {player.name}"
    description = f"<strong>{User.query.get(user_id).display_name or User.query.get(user_id).email}</strong> added <strong>{player.name}</strong> ({player.position} • {player.team}) to their roster"
    
    metadata = {
        "player_id": player.id,
        "player_name": player.name,
        "position": player.position,
        "team": player.team,
        "roster_entry_id": roster_entry.id
    }
    
    return log_activity(
        league_id=league_id,
        activity_type="roster_add",
        title=title,
        description=description,
        user_id=user_id,
        activity_metadata=metadata
    )


def log_roster_remove(league_id: int, user_id: int, player: Player) -> LeagueActivity:
    """Log a roster removal"""
    title = f"Roster Removal: {player.name}"
    description = f"<strong>{User.query.get(user_id).display_name or User.query.get(user_id).email}</strong> removed <strong>{player.name}</strong> ({player.position} • {player.team}) from their roster"
    
    metadata = {
        "player_id": player.id,
        "player_name": player.name,
        "position": player.position,
        "team": player.team
    }
    
    return log_activity(
        league_id=league_id,
        activity_type="roster_remove",
        title=title,
        description=description,
        user_id=user_id,
        activity_metadata=metadata
    )


def log_board_post(post: BoardPost) -> LeagueActivity:
    """Log a community board post"""
    title = f"New Post: {post.title}"
    description = f"<strong>{post.author.display_name or post.author.email}</strong> posted: <strong>\"{post.title}\"</strong>"
    
    # Truncate body for description
    body_preview = post.body[:100] + "..." if len(post.body) > 100 else post.body
    description += f"<br><em>{body_preview}</em>"
    
    metadata = {
        "post_id": post.id,
        "post_title": post.title,
        "has_body": bool(post.body)
    }
    
    return log_activity(
        league_id=post.league_id,
        activity_type="post_created",
        title=title,
        description=description,
        user_id=post.author_id,
        activity_metadata=metadata
    )


def log_board_post_edit(post: BoardPost) -> LeagueActivity:
    """Log a community board post edit"""
    title = f"Post Edited: {post.title}"
    description = f"<strong>{post.author.display_name or post.author.email}</strong> edited their post: <strong>\"{post.title}\"</strong>"
    
    metadata = {
        "post_id": post.id,
        "post_title": post.title
    }
    
    return log_activity(
        league_id=post.league_id,
        activity_type="post_edited",
        title=title,
        description=description,
        user_id=post.author_id,
        activity_metadata=metadata
    )


def log_board_post_delete(post: BoardPost) -> LeagueActivity:
    """Log a community board post deletion"""
    title = f"Post Deleted: {post.title}"
    description = f"<strong>{post.author.display_name or post.author.email}</strong> deleted their post: <strong>\"{post.title}\"</strong>"
    
    metadata = {
        "post_id": post.id,
        "post_title": post.title
    }
    
    return log_activity(
        league_id=post.league_id,
        activity_type="post_deleted",
        title=title,
        description=description,
        user_id=post.author_id,
        activity_metadata=metadata
    )


def get_league_activities(league_id: int, limit: int = 50) -> List[LeagueActivity]:
    """Get recent league activities"""
    return LeagueActivity.query.filter_by(league_id=league_id)\
        .order_by(LeagueActivity.created_at.desc())\
        .limit(limit)\
        .all()


def get_user_activities(user_id: int, limit: int = 20) -> List[LeagueActivity]:
    """Get recent activities for a specific user"""
    return LeagueActivity.query.filter_by(user_id=user_id)\
        .order_by(LeagueActivity.created_at.desc())\
        .limit(limit)\
        .all()


def _get_player_names_from_ids(roster_entry_ids: List[str]) -> List[str]:
    """Helper function to get player names from roster entry IDs"""
    if not roster_entry_ids or roster_entry_ids == ['']:
        return []
    
    try:
        entries = RosterEntry.query.filter(RosterEntry.id.in_(roster_entry_ids)).all()
        return [entry.player.name for entry in entries if entry.player]
    except Exception as e:
        current_app.logger.error(f"Error getting player names: {e}")
        return []


def format_activity_time(created_at: datetime) -> str:
    """Format activity timestamp for display"""
    now = datetime.utcnow()
    diff = now - created_at
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def get_activity_icon(activity_type: str) -> str:
    """Get appropriate icon for activity type"""
    icons = {
        "trade_proposal": "💼",
        "trade_accepted": "✅",
        "trade_rejected": "❌",
        "roster_add": "➕",
        "roster_remove": "➖",
        "post_created": "💬",
        "post_edited": "✏️",
        "post_deleted": "🗑️"
    }
    return icons.get(activity_type, "📝")


def get_activity_color(activity_type: str) -> str:
    """Get appropriate color class for activity type"""
    colors = {
        "trade_proposal": "activity-trade",
        "trade_accepted": "activity-success",
        "trade_rejected": "activity-danger",
        "roster_add": "activity-info",
        "roster_remove": "activity-warning",
        "post_created": "activity-primary",
        "post_edited": "activity-secondary",
        "post_deleted": "activity-danger"
    }
    return colors.get(activity_type, "activity-default")
