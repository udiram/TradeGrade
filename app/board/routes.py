from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..extensions import db
from ..models import BoardPost, Membership


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
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        if not title or not body:
            flash("Title and body required", "warning")
            return render_template("board/create.html", league_id=league_id)
        post = BoardPost(league_id=league_id, author_id=current_user.id, title=title, body=body)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("board.list_posts", league_id=league_id))
    return render_template("board/create.html", league_id=league_id)


