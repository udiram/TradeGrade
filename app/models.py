from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(UserMixin, TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120), nullable=True)

    memberships = db.relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    roster_entries = db.relationship(
        "RosterEntry", back_populates="user", cascade="all, delete-orphan"
    )
    posts = db.relationship("BoardPost", back_populates="author", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def find_by_email_or_username(identifier: str) -> Optional['User']:
        """Find user by email or username"""
        return User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()


class League(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    invite_code = db.Column(db.String(32), unique=True, nullable=False, index=True)

    memberships = db.relationship("Membership", back_populates="league", cascade="all, delete-orphan")
    posts = db.relationship("BoardPost", back_populates="league", cascade="all, delete-orphan")


class Membership(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    league_id = db.Column(db.Integer, db.ForeignKey("league.id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="memberships")
    league = db.relationship("League", back_populates="memberships")

    __table_args__ = (db.UniqueConstraint("user_id", "league_id", name="uq_user_league"),)


class Player(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    position = db.Column(db.String(10), nullable=True)
    team = db.Column(db.String(10), nullable=True)
    injury_status = db.Column(db.String(20), nullable=True)  # OUT, Doubtful, Questionable, Probable, IR
    injury_updated_at = db.Column(db.DateTime, nullable=True)


class RosterEntry(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    league_id = db.Column(db.Integer, db.ForeignKey("league.id"), nullable=False, index=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False, index=True)
    is_starter = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", back_populates="roster_entries")
    league = db.relationship("League")
    player = db.relationship("Player")

    __table_args__ = (
        db.UniqueConstraint("user_id", "league_id", "player_id", name="uq_user_league_player"),
    )


class Trade(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey("league.id"), nullable=False)
    proposer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    offered_player_ids = db.Column(db.Text, nullable=False)  # comma-separated ids
    requested_player_ids = db.Column(db.Text, nullable=False)
    numeric_score = db.Column(db.Float, nullable=True)
    recommendation = db.Column(db.String(32), nullable=True)
    summary = db.Column(db.Text, nullable=True)


class TradeProposal(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey("league.id"), nullable=False, index=True)
    proposer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    offered_player_ids = db.Column(db.Text, nullable=False)  # comma-separated roster entry ids
    requested_player_ids = db.Column(db.Text, nullable=False)  # comma-separated roster entry ids
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending, accepted, rejected, cancelled
    message = db.Column(db.Text, nullable=True)  # optional message from proposer
    analysis_data = db.Column(db.Text, nullable=True)  # JSON string of trade analysis
    
    # Relationships
    league = db.relationship("League")
    proposer = db.relationship("User", foreign_keys=[proposer_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])


class BoardPost(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey("league.id"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)

    league = db.relationship("League", back_populates="posts")
    author = db.relationship("User", back_populates="posts")


class LeagueActivity(TimestampMixin, db.Model):
    """Track all league activities for the activity feed"""
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey("league.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)  # Can be null for system events
    activity_type = db.Column(db.String(50), nullable=False, index=True)  # trade_proposal, trade_accepted, trade_rejected, roster_add, roster_remove, post_created, post_edited, post_deleted
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    activity_data = db.Column(db.Text, nullable=True)  # JSON string for additional data (player names, trade details, etc.)
    
    # Relationships
    league = db.relationship("League", backref="activities")
    user = db.relationship("User", backref="activities")


