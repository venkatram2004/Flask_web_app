from routes.api import api_bp
from routes.summary import summary_bp
from routes.transactions import transactions_bp
from routes.auth import auth_bp
from database import init_db
from flask_cors import CORS
from flask import Flask, redirect, url_for
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


app = Flask(__name__)
app.secret_key = "finance_tracker_secret_key_2026"

CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(summary_bp)
app.register_blueprint(api_bp)


@app.route('/')
def index():
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
