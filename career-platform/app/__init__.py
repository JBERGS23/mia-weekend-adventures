"""Flask application factory.

Creating the app in a function rather than at import time keeps the tests able
to build a throwaway app against a temporary database.
"""

from __future__ import annotations

from flask import Flask

import config


def create_app(testing: bool = False) -> Flask:
    app = Flask(
        __name__,
        template_folder="web/templates",
        static_folder="web/static",
    )
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["TESTING"] = testing
    # Templates re-read on each request during development; harmless locally.
    app.jinja_env.auto_reload = True

    from app import db, seed

    db.init_db()
    with db.session() as conn:
        seed.seed_all(conn)
        # Make sure priorities exist even on a database seeded by an older
        # version that predates the gap engine.
        from app.gap import engine

        if db.scalar(conn, "SELECT COUNT(*) FROM gap_history", (), 0) == 0:
            engine.recompute(conn, reason="first run")

    from app.web.routes_main import bp as main_bp
    from app.web.routes_jobs import bp as jobs_bp
    from app.web.routes_academy import bp as academy_bp
    from app.web.routes_networking import bp as networking_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(academy_bp)
    app.register_blueprint(networking_bp)

    from app.web import filters

    filters.register(app)

    return app
