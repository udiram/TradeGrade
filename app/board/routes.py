from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from ..extensions import db
from ..models import BoardPost, Membership, User
import re


board_bp = Blueprint("board", __name__, url_prefix="/board")


@board_bp.route("/<int:league_id>")
@login_required
def list_posts(league_id: int):
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    posts = BoardPost.query.filter_by(league_id=league_id).order_by(BoardPost.created_at.desc()).all()
    return render_template("board/list.html", league_id=league_id, posts=posts)


@board_bp.route("/<int:league_id>/create", methods=["GET", "POST"]) 
@login_required
def create_post(league_id: int):
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get league members for tagging
    league_members = User.query.join(Membership).filter(Membership.league_id == league_id).all()
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        if not title or not body:
            flash("Title and body required", "warning")
            return render_template("board/create.html", league_id=league_id, league_members=league_members)
        
        # Process tags in the body
        processed_body = process_tags(body, league_id)
        
        post = BoardPost(league_id=league_id, author_id=current_user.id, title=title, body=processed_body)
        db.session.add(post)
        db.session.commit()
        flash("Post created successfully", "success")
        return redirect(url_for("board.list_posts", league_id=league_id))
    
    return render_template("board/create.html", league_id=league_id, league_members=league_members)


@board_bp.route("/<int:league_id>/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(league_id: int, post_id: int):
    # Check membership
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get the post
    post = BoardPost.query.filter_by(id=post_id, league_id=league_id).first_or_404()
    
    # Check if user is the author
    if post.author_id != current_user.id:
        flash("You can only edit your own posts", "danger")
        return redirect(url_for("board.list_posts", league_id=league_id))
    
    # Get league members for tagging
    league_members = User.query.join(Membership).filter(Membership.league_id == league_id).all()
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        if not title or not body:
            flash("Title and body required", "warning")
            return render_template("board/edit.html", league_id=league_id, post=post, league_members=league_members)
        
        # Process tags in the body
        processed_body = process_tags(body, league_id)
        
        post.title = title
        post.body = processed_body
        db.session.commit()
        flash("Post updated successfully", "success")
        return redirect(url_for("board.list_posts", league_id=league_id))
    
    return render_template("board/edit.html", league_id=league_id, post=post, league_members=league_members)


@board_bp.route("/<int:league_id>/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(league_id: int, post_id: int):
    # Check membership
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"error": "Not a member of this league"}), 403
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get the post
    post = BoardPost.query.filter_by(id=post_id, league_id=league_id).first_or_404()
    
    # Check if user is the author
    if post.author_id != current_user.id:
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"error": "Can only delete your own posts"}), 403
        flash("You can only delete your own posts", "danger")
        return redirect(url_for("board.list_posts", league_id=league_id))
    
    # Delete the post
    db.session.delete(post)
    db.session.commit()
    
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({"success": True, "message": "Post deleted successfully"})
    
    flash("Post deleted successfully", "success")
    return redirect(url_for("board.list_posts", league_id=league_id))


def process_tags(body: str, league_id: int) -> str:
    """Process @mentions in the body text and convert them to clickable links"""
    # Get all league members
    league_members = User.query.join(Membership).filter(Membership.league_id == league_id).all()
    
    # Create a mapping of display names and emails to user IDs
    member_map = {}
    for member in league_members:
        display_name = member.display_name or member.email.split('@')[0]
        member_map[display_name.lower()] = member.id
        member_map[member.email.lower()] = member.id
        # Also map email username part
        email_username = member.email.split('@')[0]
        member_map[email_username.lower()] = member.id
    
    # Find all @mentions
    mention_pattern = r'@(\w+(?:\.\w+)*@?\w*)'
    
    def replace_mention(match):
        mention = match.group(1)
        mention_lower = mention.lower()
        
        # Check if it's a valid member
        if mention_lower in member_map:
            user_id = member_map[mention_lower]
            return f'<a href="/league/{league_id}/team/{user_id}" class="mention-link">@{mention}</a>'
        else:
            # Return original if not found
            return f'@{mention}'
    
    # Replace mentions with links
    processed_body = re.sub(mention_pattern, replace_mention, body)
    
    return processed_body


