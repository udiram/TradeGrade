import secrets

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..extensions import db
from ..models import League, Membership


league_bp = Blueprint("league", __name__, url_prefix="/league")


@league_bp.route("/dashboard")
@login_required
def dashboard():
    memberships = Membership.query.filter_by(user_id=current_user.id).all()
    return render_template("league/dashboard.html", memberships=memberships)


@league_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("League name required", "warning")
            return render_template("league/create.html")
        invite_code = secrets.token_urlsafe(8)
        league = League(name=name, invite_code=invite_code)
        db.session.add(league)
        db.session.flush()
        db.session.add(Membership(user_id=current_user.id, league_id=league.id))
        db.session.commit()
        flash("League created", "success")
        return redirect(url_for("league.dashboard"))
    return render_template("league/create.html")


@league_bp.route("/join", methods=["GET", "POST"])
@login_required
def join():
    if request.method == "POST":
        code = request.form.get("invite_code", "").strip()
        league = League.query.filter_by(invite_code=code).first()
        if not league:
            flash("Invalid invite code", "danger")
            return render_template("league/join.html")
        existing = Membership.query.filter_by(user_id=current_user.id, league_id=league.id).first()
        if existing:
            flash("Already a member", "info")
            return redirect(url_for("league.dashboard"))
        db.session.add(Membership(user_id=current_user.id, league_id=league.id))
        db.session.commit()
        flash("Joined league", "success")
        return redirect(url_for("league.dashboard"))
    return render_template("league/join.html")


