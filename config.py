import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.abspath('app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional external APIs for analysis/sentiment
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
    TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")
    # OAuth
    OAUTH_GOOGLE_CLIENT_ID = os.environ.get("OAUTH_GOOGLE_CLIENT_ID")
    OAUTH_GOOGLE_CLIENT_SECRET = os.environ.get("OAUTH_GOOGLE_CLIENT_SECRET")
    OAUTH_GOOGLE_REDIRECT_URI = os.environ.get("OAUTH_GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback")

    # Email/Magic link
    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    SMTP_FROM = os.environ.get("SMTP_FROM", "no-reply@tradegrade.dev")

    # Socket.IO
    SOCKETIO_MESSAGE_QUEUE = os.environ.get("SOCKETIO_MESSAGE_QUEUE")


