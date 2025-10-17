from flask import Flask, render_template, redirect, url_for
from flask import request
from .extensions import db, migrate, login_manager, socketio
from .models import User
from config import Config


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    register_extensions(app)
    register_blueprints(app)
    register_routes(app)
    
    # Only run startup tasks when not in CLI mode
    import sys
    if 'flask' not in sys.argv:
        run_startup_tasks(app)

    return app


def register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"))
    # No OAuth providers configured

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.login"


def register_blueprints(app: Flask) -> None:
    from .auth.routes import auth_bp
    from .league.routes import league_bp
    from .roster.routes import roster_bp
    from .trades.routes import trades_bp
    from .board.routes import board_bp
    from .api.routes import api_bp
    from .trade_proposals.routes import trade_proposals_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(league_bp)
    app.register_blueprint(roster_bp)
    app.register_blueprint(trades_bp)
    app.register_blueprint(board_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(trade_proposals_bp)


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return render_template("index.html")

    @socketio.on('join')
    def on_join(data):
        room = data.get('room')
        print(f"Client joining room: {room}")
        if room:
            from flask_socketio import join_room
            join_room(room)
            print(f"Client successfully joined room: {room}")

    @socketio.on('leave')
    def on_leave(data):
        room = data.get('room')
        print(f"Client leaving room: {room}")
        if room:
            from flask_socketio import leave_room
            leave_room(room)
            print(f"Client successfully left room: {room}")


def run_startup_tasks(app: Flask) -> None:
    with app.app_context():
        from .services.players import warm_players_cache, sync_active_players_into_db, purge_non_nfl_players
        from .models import Player
        
        # Warm the cache first
        warm_players_cache()
        
        # Sync all active NFL players to database
        print("Syncing NFL players to database...")
        removed = purge_non_nfl_players(db, Player)
        added = sync_active_players_into_db(db, Player)
        print(f"Player sync complete: {removed} removed, {added} added")

