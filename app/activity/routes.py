"""
Activity feed routes
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import League, Membership, LeagueActivity
from app.services.activity import get_league_activities, format_activity_time, get_activity_icon, get_activity_color
import json

activity_bp = Blueprint('activity', __name__, url_prefix='/activity')


@activity_bp.route("/<int:league_id>")
@login_required
def league_activity(league_id: int):
    """Display league activity feed"""
    # Check membership
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        return jsonify({"error": "You are not a member of this league"}), 403
    
    # Get league
    league = League.query.get_or_404(league_id)
    
    # Get activities
    activities = get_league_activities(league_id, limit=50)
    
    # Format activities for display
    formatted_activities = []
    for activity in activities:
        formatted_activities.append({
            "id": activity.id,
            "type": activity.activity_type,
            "title": activity.title,
            "description": activity.description,
            "user": activity.user.display_name or activity.user.email if activity.user else "System",
            "user_id": activity.user_id,
            "created_at": activity.created_at,
            "time_ago": format_activity_time(activity.created_at),
            "icon": get_activity_icon(activity.activity_type),
            "color_class": get_activity_color(activity.activity_type),
            "metadata": json.loads(activity.activity_data) if activity.activity_data else {}
        })
    
    return render_template("activity/feed.html", 
                         league=league, 
                         activities=formatted_activities)


@activity_bp.route("/<int:league_id>/api")
@login_required
def league_activity_api(league_id: int):
    """API endpoint for league activity feed (for AJAX updates)"""
    # Check membership
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        return jsonify({"error": "You are not a member of this league"}), 403
    
    # Get limit from query params
    limit = request.args.get('limit', 20, type=int)
    
    # Get activities
    activities = get_league_activities(league_id, limit=limit)
    
    # Format activities for JSON response
    formatted_activities = []
    for activity in activities:
        formatted_activities.append({
            "id": activity.id,
            "type": activity.activity_type,
            "title": activity.title,
            "description": activity.description,
            "user": activity.user.display_name or activity.user.email if activity.user else "System",
            "user_id": activity.user_id,
            "created_at": activity.created_at.isoformat(),
            "time_ago": format_activity_time(activity.created_at),
            "icon": get_activity_icon(activity.activity_type),
            "color_class": get_activity_color(activity.activity_type),
            "metadata": json.loads(activity.activity_data) if activity.activity_data else {}
        })
    
    return jsonify({
        "activities": formatted_activities,
        "count": len(formatted_activities)
    })


@activity_bp.route("/<int:league_id>/latest")
@login_required
def latest_activity(league_id: int):
    """Get latest activity for real-time updates"""
    # Check membership
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        return jsonify({"error": "You are not a member of this league"}), 403
    
    # Get latest activity
    latest_activity = LeagueActivity.query.filter_by(league_id=league_id)\
        .order_by(LeagueActivity.created_at.desc())\
        .first()
    
    if not latest_activity:
        return jsonify({"activity": None})
    
    return jsonify({
        "activity": {
            "id": latest_activity.id,
            "type": latest_activity.activity_type,
            "title": latest_activity.title,
            "description": latest_activity.description,
            "user": latest_activity.user.display_name or latest_activity.user.email if latest_activity.user else "System",
            "user_id": latest_activity.user_id,
            "created_at": latest_activity.created_at.isoformat(),
            "time_ago": format_activity_time(latest_activity.created_at),
            "icon": get_activity_icon(latest_activity.activity_type),
            "color_class": get_activity_color(latest_activity.activity_type),
            "metadata": json.loads(latest_activity.metadata) if latest_activity.metadata else {}
        }
    })
