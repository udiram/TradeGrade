import os
from app import create_app, socketio


app = create_app()


if __name__ == "__main__":
    # Use eventlet/gevent in production for websockets
    port = int(os.environ.get("PORT", "5050"))
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)


