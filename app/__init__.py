from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    with app.app_context():
        from app import models
        db.create_all()

    # Register blueprints
    from app.routes.health import bp as health_bp
    app.register_blueprint(health_bp)

    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.medicine import bp as medicine_bp
    app.register_blueprint(medicine_bp)

    from app.routes.supply import bp as supply_bp
    app.register_blueprint(supply_bp)

    from app.routes.verify import bp as verify_bp
    app.register_blueprint(verify_bp)

    from app.routes.search import bp as search_bp
    app.register_blueprint(search_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app
