from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db
from ..models import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = User.find_by_email_or_username(identifier)
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("league.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        display_name = request.form.get("display_name")
        
        # Validate username format
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash("Username can only contain letters, numbers, and underscores", "warning")
            return render_template("auth/register.html")
        
        if len(username) < 3 or len(username) > 50:
            flash("Username must be between 3 and 50 characters", "warning")
            return render_template("auth/register.html")
        
        # Check if email or username already exists
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "warning")
            return render_template("auth/register.html")
        
        if User.query.filter_by(username=username).first():
            flash("Username already taken", "warning")
            return render_template("auth/register.html")
        
        user = User(email=email, username=username, display_name=display_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("league.dashboard"))
    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


# OAuth and Magic link removed; using only email/password auth


