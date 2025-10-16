import secrets

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..extensions import db
from ..models import League, Membership, User, RosterEntry, Player


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


@league_bp.route("/<int:league_id>/members")
@login_required
def view_members(league_id: int):
    # Check if user is a member of this league
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get league info
    league = League.query.get_or_404(league_id)
    
    # Get all members with their roster data
    memberships = Membership.query.filter_by(league_id=league_id).all()
    members_data = []
    
    for mem in memberships:
        user = mem.user
        roster_entries = RosterEntry.query.filter_by(user_id=user.id, league_id=league_id).all()
        
        # Separate starters and bench
        starters = [entry for entry in roster_entries if entry.is_starter]
        bench = [entry for entry in roster_entries if not entry.is_starter]
        
        members_data.append({
            'user': user,
            'starters': starters,
            'bench': bench,
            'total_players': len(roster_entries)
        })
    
    return render_template("league/members.html", league=league, members_data=members_data)


