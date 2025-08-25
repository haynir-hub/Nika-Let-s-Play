# lesson_app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "app.db")

db = SQLAlchemy()
login_manager = LoginManager()

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "please-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "routes.login"
    login_manager.login_message = None  # בלי פסי אזהרה צהובים

    from lesson_app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    from lesson_app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    # יצירת טבלאות + אדמין ברירת מחדל (Hay) אם אין משתמשים
    with app.app_context():
        db.create_all()
        try:
            if User.query.count() == 0:
                admin_password = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")
                u = User(username="Hay")
                u.set_password(admin_password)
                db.session.add(u)
                db.session.commit()
        except Exception:
            db.session.rollback()

    return app

app = create_app()
