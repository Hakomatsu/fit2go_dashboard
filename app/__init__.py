from datetime import datetime

import pytz
from flask import Flask
from flask_migrate import Migrate

from config.config import config

from .models import db, init_db


def create_app(config_name="default"):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Initialize database
    init_db(app)

    # Set timezone
    app.timezone = pytz.timezone(app.config["TIMEZONE"])

    # Register blueprints
    from .routes import api, main

    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp, url_prefix="/api")

    @app.context_processor
    def utility_processor():
        def format_datetime(value, format="%Y-%m-%d %H:%M:%S"):
            if value is None:
                return ""
            if not isinstance(value, datetime):
                return value
            local_dt = value.astimezone(app.timezone)
            return local_dt.strftime(format)

        return dict(format_datetime=format_datetime)

    return app
