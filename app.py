import os
from flask import Flask
from extensions import db, migrate
from routes import configure_routes  # this is fine here

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Config
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///check_management.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Init extensions
db.init_app(app)
migrate.init_app(app, db)

with app.app_context():
    import models
    db.create_all()

configure_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
