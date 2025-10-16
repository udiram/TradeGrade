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

    app.register_blueprint(auth_bp)
    app.register_blueprint(league_bp)
    app.register_blueprint(roster_bp)
    app.register_blueprint(trades_bp)
    app.register_blueprint(board_bp)
    app.register_blueprint(api_bp)


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return render_template("index.html")

    @socketio.on('join')
    def on_join(data):
        room = data.get('room')
        if room:
            from flask_socketio import join_room
            join_room(room)

    @socketio.on('leave')
    def on_leave(data):
        room = data.get('room')
        if room:
            from flask_socketio import leave_room
            leave_room(room)


def run_startup_tasks(app: Flask) -> None:
    with app.app_context():
        from .seed import seed_players_if_empty
        from .services.players import warm_players_cache
        seed_players_if_empty()
        warm_players_cache()


